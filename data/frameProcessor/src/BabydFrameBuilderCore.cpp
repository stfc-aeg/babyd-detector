// #include "X10GProtocol.h"
#include "BabydFrameBuilderCore.h"
#include "DpdkSharedBufferFrame.h"
#include "DpdkUtils.h"
#include "DpdkSharedBufferFrame.h"

#define COARSE_MASK 0x00FF
#define OVERFLOW_MASK 0x0100
#define FINE_MASK 0xFE00

namespace FrameProcessor
{
    BabydFrameBuilderCore::BabydFrameBuilderCore(
        int fb_idx, int socket_id, DpdkWorkCoreReferences &dpdkWorkCoreReferences
                                        ) : DpdkWorkerCore(socket_id),
                                        logger_(Logger::getLogger("FP.BabydFrameBuilderCore")),
                                        proc_idx_(fb_idx),
                                        decoder_(dpdkWorkCoreReferences.decoder),
                                        shared_buf_(dpdkWorkCoreReferences.shared_buf),
                                        built_frames_(0),
                                        built_frames_hz_(1),
                                        idle_loops_(0),
                                        mean_us_on_frame_(0),
                                        maximum_us_on_frame_(0),
                                        core_usage_(1),
                                        out_of_order_frames_(0),
                                        in_order_frames_(0)
    {

        // Get the configuration container for this worker
        config_.resolve(dpdkWorkCoreReferences.core_config);
       
       LOG4CXX_INFO(logger_, "FP.BabydFrameBuilderCore " << proc_idx_ << " Created with config:"
            << " | core_name" << config_.core_name
            << " | num_cores: " << config_.num_cores
            << " | connect: " << config_.connect
            << " | upstream_core: " << config_.upstream_core
            << " | num_downsteam_cores: " << config_.num_downstream_cores
        );

        // Check if the downstream ring have already been created by another processing core,
        // otherwise create it with the ring size rounded up to the next power of two
        for (int ring_idx = 0; ring_idx < config_.num_downstream_cores; ring_idx++)
        {
            std::string downstream_ring_name = ring_name_str(config_.core_name, socket_id_, ring_idx);
            struct rte_ring* downstream_ring = rte_ring_lookup(downstream_ring_name.c_str());
            if (downstream_ring == NULL)
            {
                unsigned int downstream_ring_size = nearest_power_two(shared_buf_->get_num_buffers());
                LOG4CXX_INFO(logger_, "Creating ring name "
                    << downstream_ring_name << " of size " << downstream_ring_size
                );
                downstream_ring = rte_ring_create(
                    downstream_ring_name.c_str(), downstream_ring_size, socket_id_, 0
                );
                if (downstream_ring == NULL)
                {
                    LOG4CXX_ERROR(logger_, "Error creating downstream ring " << downstream_ring_name
                        << " : " << rte_strerror(rte_errno)
                    );
                    // TODO - this is fatal and should raise an exception
                }
            }
            else
            {
                LOG4CXX_DEBUG_LEVEL(2, logger_, "downstream ring with name "
                    << downstream_ring_name << " has already been created"
                );
            }
            if (downstream_ring)
            {
                downstream_rings_.push_back(downstream_ring);
            }

        }

    }

    BabydFrameBuilderCore::~BabydFrameBuilderCore(void)
    {
        LOG4CXX_DEBUG_LEVEL(2, logger_, "BabydFrameBuilderCore destructor");
        std::cout << "FBC Destory" << std::endl;
        stop();
    }

    

    bool BabydFrameBuilderCore::run(unsigned int lcore_id)
    {

        lcore_id_ = lcore_id;
        run_lcore_ = true;

        LOG4CXX_INFO(logger_, "Core " << lcore_id_ << " starting up");

        // Generic frame variables
        struct SuperFrameHeader *current_super_frame_buffer_;
        dimensions_t dims(2);

        // Specific frame variables from decoder

        dims[0] = decoder_->get_frame_x_resolution();
        dims[1] = decoder_->get_frame_y_resolution();
        std::size_t frame_size =
            dims[0] * dims[1] * get_size_from_enum(decoder_->get_frame_bit_depth());
        std::size_t frame_header_size = decoder_->get_frame_header_size();
        std::size_t payload_size = decoder_->get_payload_size();

        // Status reporting variables
        bool first_frame = true;
        uint64_t prev_frame_number = 1;
        uint64_t frame_number = 1;

        // Status reporting variables
        uint64_t frames_per_second = 1;
        uint64_t last = rte_get_tsc_cycles();
        uint64_t cycles_per_sec = rte_get_tsc_hz();
        uint64_t cycles_working = 1;
        uint64_t start_frame_cycles = 1;
        uint64_t average_frame_cycles = 1;
        uint64_t total_frame_cycles = 1;
        uint64_t maximum_frame_cycles = 1;

        // Create a buffer for a single frame, we set this to zero on creation
        uint16_t frame_buffer[256] = { 0 };

        LOG4CXX_INFO(logger_, "Decoder static information:");
        LOG4CXX_INFO(logger_, "get_frame_x_resolution: " << decoder_->get_frame_x_resolution());
        LOG4CXX_INFO(logger_, "get_frame_y_resolution: " << decoder_->get_frame_y_resolution());
        LOG4CXX_INFO(logger_, "get_frame_outer_chunk_size: " << decoder_->get_frame_outer_chunk_size());
        LOG4CXX_INFO(logger_, "get_frame_bit_depth: " << static_cast<int>(decoder_->get_frame_bit_depth()));
        LOG4CXX_INFO(logger_, "get_super_frame_header_size: " << decoder_->get_super_frame_header_size());
        LOG4CXX_INFO(logger_, "get_frame_header_size: " << decoder_->get_frame_header_size());
        LOG4CXX_INFO(logger_, "get_frame_data_size: " << decoder_->get_frame_data_size());
        LOG4CXX_INFO(logger_, "get_frame_buffer_size: " << decoder_->get_frame_buffer_size());
        LOG4CXX_INFO(logger_, "get_packet_header_size: " << decoder_->get_packet_header_size());


        // While loop to continuously dequeue frame objects
        while (likely(run_lcore_))
        {
            uint64_t now = rte_get_tsc_cycles();
            if (unlikely((now - last) >= (cycles_per_sec)))
            {
                // Update any monitoring variables every second
                built_frames_hz_ = frames_per_second - 1;
                mean_us_on_frame_ = (total_frame_cycles * 1000000) / (frames_per_second * cycles_per_sec);
                core_usage_ = (cycles_working * 255) / cycles_per_sec;

                maximum_us_on_frame_ = (maximum_frame_cycles * 1000000) / (cycles_per_sec);

                // Reset any counters
                frames_per_second = 1;
                idle_loops_ = 0;
                total_frame_cycles = 1;
                cycles_working = 1;
                last = now;
            }
            // Attempt to dequeue a new frame object
            if (rte_ring_dequeue(upstream_ring, (void **)&current_super_frame_buffer_) < 0)
            {
                // No frame was dequeued, try again
                idle_loops_++;
                continue;
            }
            else
            {
                start_frame_cycles = rte_get_tsc_cycles();
                frame_number = decoder_->get_super_frame_number(current_super_frame_buffer_);

                if((prev_frame_number + 1) == frame_number)
                {
                    in_order_frames_++;
                }
                else
                {
                    out_of_order_frames_++;
                }

                prev_frame_number = frame_number;


                // Get a pointer to the start of the raw data
                uint16_t* raw_data_ptr = (uint16_t*)decoder_->get_image_data_start(current_super_frame_buffer_);
                // Calculate the start of the built data, this should be past where the raw data is held
                uint16_t* built_data_ptr = raw_data_ptr + (16 * 16 * 1000);

                

                // Calculate the number of pixels in a single frame
                size_t pixels_per_frame = decoder_->get_frame_x_resolution() * decoder_->get_frame_y_resolution();

                //  LOG4CXX_INFO(logger_, "Core " << lcore_id_
                //     << "Starting rebuild of frame: "
                //     << " Raw data pointer: " << raw_data_ptr
                //     << " Built data pointer: " << built_data_ptr
                //     << " Diff: " << built_data_ptr - raw_data_ptr
                
                //     );


                // LOG4CXX_INFO(logger_, "Frame information:");
                // LOG4CXX_INFO(logger_, "current_super_frame_buffer_: " << current_super_frame_buffer_);
                // LOG4CXX_INFO(logger_, "get_image_data_start: " << (uint16_t*) decoder_->get_image_data_start(current_super_frame_buffer_));
                // LOG4CXX_INFO(logger_, "raw_data_ptr: " << raw_data_ptr);
                // LOG4CXX_INFO(logger_, "built_data_ptr: " << built_data_ptr);
                // LOG4CXX_INFO(logger_, "raw_data_ptr - current_super_frame_buffer_: " << raw_data_ptr - (uint16_t*) current_super_frame_buffer_);
                // LOG4CXX_INFO(logger_, "built_data_ptr - current_super_frame_buffer_: " << built_data_ptr - (uint16_t*) current_super_frame_buffer_);
                // LOG4CXX_INFO(logger_, "get_image_data_start - current_super_frame_buffer_: " << decoder_->get_image_data_start(current_super_frame_buffer_) - (char*) current_super_frame_buffer_);
                // LOG4CXX_INFO(logger_, "get_frame_buffer_size " << decoder_->get_frame_buffer_size());



                // memset(raw_data_ptr, 85, 16 * 16 * 2 * 1000 * 2);

                // memset(built_data_ptr, 170, 16 * 16 * 2 * 1000);

                // For each frame in the super frame
                for (int frame = 0; frame < decoder_->get_frame_outer_chunk_size(); frame++)
                {
                    // Loop over every pixel in the frame
                    for (size_t pixel = 0; pixel < pixels_per_frame; pixel++)
                    {
                        if (frame == 0)
                        {
                            // Combine with the buffered frame for the first frame
                            built_data_ptr[pixel] = (frame_buffer[pixel] & (COARSE_MASK | OVERFLOW_MASK)) | (raw_data_ptr[pixel] & FINE_MASK);
                        }                      
                        else
                        {
                            // Combine the frame with the one before it
                            built_data_ptr[pixel] = (raw_data_ptr[pixel - pixels_per_frame] & (COARSE_MASK | OVERFLOW_MASK)) | (raw_data_ptr[pixel] & FINE_MASK);
                        }
                    }

                    // Move pointers to the next frame
                    raw_data_ptr += pixels_per_frame;
                    built_data_ptr += pixels_per_frame;
                }

                rte_memcpy(&frame_buffer, raw_data_ptr - pixels_per_frame, pixels_per_frame * 2);


                // rte_memcpy(built_data_ptr, raw_data_ptr, decoder_->get_frame_data_size() * decoder_->get_frame_outer_chunk_size());


                // LOG4CXX_INFO(logger_, "Core " << lcore_id_
                //     << " Finished rebuilt of frame"
                //     << " Raw data pointer: " << raw_data_ptr
                //     << " Built data pointer: " << built_data_ptr
                //     << " Diff: " << built_data_ptr - raw_data_ptr
                
                //     );

            

                // Enqueue the built frame object to the next set of cores
                rte_ring_enqueue(
                    downstream_rings_[frame_number % (config_.num_downstream_cores)], current_super_frame_buffer_);
                

                // Update status
                uint64_t cycles_spent = rte_get_tsc_cycles() - start_frame_cycles;
                total_frame_cycles += cycles_spent;
                cycles_working += cycles_spent;
                
                if (maximum_frame_cycles < cycles_spent)
                {
                    maximum_frame_cycles = cycles_spent;
                }
                

                frames_per_second++;
                built_frames_++;
            }
        }

        LOG4CXX_INFO(logger_, "Core " << lcore_id_ << " completed");

        return true;
    }

    void BabydFrameBuilderCore::stop(void)
    {
        if (run_lcore_)
        {
            LOG4CXX_INFO(logger_, "Core " << lcore_id_ << " stopping");
            run_lcore_ = false;
        }
        else
        {
            LOG4CXX_DEBUG_LEVEL(2, logger_, "Core " << lcore_id_ << " already stopped");
        }
    }

    void BabydFrameBuilderCore::status(OdinData::IpcMessage &status, const std::string &path)
    {
        LOG4CXX_DEBUG(logger_, "Status requested for BabydFrameBuilderCore_" << proc_idx_
                                                                        << " from the DPDK plugin");

        std::string status_path = path + "/BabydFrameBuilderCore_" + std::to_string(proc_idx_) + "/";

        // Create path for updstream ring status
        std::string ring_status = status_path + "upstream_rings/";

        // Create path for timing status
        std::string timing_status = status_path + "timing/";

        // Frame status reporting
        status.set_param(status_path + "frames_processes", built_frames_);
        status.set_param(status_path + "frames_processed_per_second", built_frames_hz_);
        status.set_param(status_path + "idle_loops", idle_loops_);
        status.set_param(status_path + "core_useage", (int)core_usage_);

        // Core timing status reporting
        status.set_param(timing_status + "mean_frame_us", mean_us_on_frame_);
        status.set_param(timing_status + "max_frame_us", maximum_us_on_frame_);

        // Upstream ring status
        status.set_param(ring_status + ring_name_str(config_.upstream_core, socket_id_, proc_idx_) + "_count", rte_ring_count(upstream_ring));
        status.set_param(ring_status + ring_name_str(config_.upstream_core, socket_id_, proc_idx_) + "_size", rte_ring_get_size(upstream_ring));
    }

    bool BabydFrameBuilderCore::connect(void)
    {

        // connect to the ring for incoming packets
        std::string upstream_ring_name = ring_name_str(config_.upstream_core, socket_id_, proc_idx_);
        upstream_ring = rte_ring_lookup(upstream_ring_name.c_str());
        if (upstream_ring == NULL)
        {
            // this needs to error out as there should always be upstream resources at this point
            LOG4CXX_INFO(logger_, config_.core_name << " : " << proc_idx_ << " Failed to Connect to upstream resources!");
            return false;
        }
        else
        {
            LOG4CXX_DEBUG_LEVEL(2, logger_, "Frame ready ring with name "
                << upstream_ring_name << " has already been created"
            );  
        }

        // connect to the ring for new memory locations packets
        std::string clear_frames_ring_name = ring_name_clear_frames(socket_id_);
        clear_frames_ring_ = rte_ring_lookup(clear_frames_ring_name.c_str());
        if (clear_frames_ring_ == NULL)
        {
            // this needs to error out as there should always be upstream resources at this point
            LOG4CXX_INFO(logger_, config_.core_name << " : " << proc_idx_ << " Failed to Connect to upstream resources!");
            return false;
        }
        else
        {
            LOG4CXX_DEBUG_LEVEL(2, logger_, "Frame ready ring with name "
                << upstream_ring_name << " has already been created"
            );  
        }

        LOG4CXX_INFO(logger_, config_.core_name << " : " << proc_idx_ << " Connected to upstream resources successfully!");

        return true;
    }



    void BabydFrameBuilderCore::configure(OdinData::IpcMessage& config)
    {
        // Update the config based from the passed IPCmessage

        LOG4CXX_INFO(logger_, config_.core_name << " : " << proc_idx_ << " Got update config.");

    }

    DPDKREGISTER(DpdkWorkerCore, BabydFrameBuilderCore, "BabydFrameBuilderCore");
}
