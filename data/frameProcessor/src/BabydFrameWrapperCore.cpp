#include "BabydFrameWrapperCore.h"
#include "DpdkUtils.h"
#include <blosc.h>
#include "DpdkSharedBufferFrame.h"
#include </usr/lib/x86_64-linux-gnu/hdf5/serial/include/hdf5.h>

namespace FrameProcessor
{
    BabydFrameWrapperCore::BabydFrameWrapperCore(
        int fb_idx, int socket_id, DpdkWorkCoreReferences &dpdkWorkCoreReferences
    ) :
        DpdkWorkerCore(socket_id),
        logger_(Logger::getLogger("FP.BabydFrameWrapperCore")),
        proc_idx_(fb_idx),
        decoder_(dpdkWorkCoreReferences.decoder),
        frame_callback_(dpdkWorkCoreReferences.frame_callback),
        processed_frames_(0),
        processed_frames_hz_(0),
        idle_loops_(0),
        mean_us_on_frame_(1),
        maximum_us_on_frame_(1),
        core_usage_(1),
        last_frame_(-1)
    {

        // Get the configuration container for this worker
        config_.resolve(dpdkWorkCoreReferences.core_config);

        LOG4CXX_INFO(logger_, "FP.BabydFrameWrapperCore " << proc_idx_ << " Created with config:"
            << " | core_name" << config_.core_name
            << " | num_cores: " << config_.num_cores
            << " | connect: " << config_.connect
            << " | upstream_core: " << config_.upstream_core
            << " | num_downsteam_cores: " << config_.num_downstream_cores
        );

    }

    BabydFrameWrapperCore::~BabydFrameWrapperCore(void)
    {
        LOG4CXX_DEBUG_LEVEL(2, logger_, "BabydFrameWrapperCore destructor");
        stop();
    }

    bool BabydFrameWrapperCore::run(unsigned int lcore_id)
    {

        lcore_id_ = lcore_id;
        run_lcore_ = true;

        LOG4CXX_INFO(logger_, "Core " << lcore_id_ << " starting up");

        // Blosc compression settings
        const char * p_compressor_name;
        blosc_compcode_to_compname(1, &p_compressor_name);

        // Frame variables
        struct SuperFrameHeader *current_super_frame_buffer_;
        struct SuperFrameHeader *built_frame_buffer;
        dimensions_t dims(2);

        // Specific frame variables from decoder
        dims[0] = decoder_->get_frame_x_resolution();
        dims[1] = decoder_->get_frame_y_resolution();
                std::size_t frame_size = decoder_->get_frame_data_size() * decoder_->get_frame_outer_chunk_size();
            //dims[0] * dims[1] * get_size_from_enum(decoder_->get_frame_bit_depth());
        std::size_t frame_header_size = decoder_->get_frame_header_size();

        // Status reporting variables
        uint64_t last_Frame = -1;
        uint64_t data_pointer_offset = (decoder_->get_frame_header_size() * decoder_->get_frame_outer_chunk_size()) + decoder_->get_super_frame_header_size();

        // Status reporting variables
        uint64_t frames_per_second = 1;
        uint64_t last = rte_get_tsc_cycles();
        uint64_t cycles_per_sec = rte_get_tsc_hz();
        uint64_t cycles_working = 1;
        uint64_t start_frame_cycles = 1;
        uint64_t average_frame_cycles = 1;
        uint64_t total_frame_cycles = 1;
        uint64_t maximum_frame_cycles = 1;
        uint64_t idle_loops = 0;

        //While loop to continuously dequeue frame objects
        while (likely(run_lcore_))
        {
            uint64_t now = rte_get_tsc_cycles();
            if (unlikely((now - last) >= (cycles_per_sec)))
            {
                // Update any monitoring variables every second
                processed_frames_hz_ = frames_per_second - 1;
                mean_us_on_frame_ = (total_frame_cycles * 1000000) / (frames_per_second * cycles_per_sec);
                core_usage_ = (cycles_working * 255) / cycles_per_sec;

                maximum_us_on_frame_ = (maximum_frame_cycles * 1000000) / (cycles_per_sec);

                idle_loops_ = idle_loops;

                // Reset any counters
                frames_per_second = 1;
                idle_loops = 0;
                total_frame_cycles = 1;
                cycles_working = 1;
                last = now;
            }
            // Attempt to dequeue a new frame object
            if (rte_ring_dequeue(upstream_ring_, (void**) &current_super_frame_buffer_) < 0)
            {
                // No frame was dequeued, try again
                idle_loops_++;
                continue;
            }
            else
            {
                start_frame_cycles = rte_get_tsc_cycles();

                // Get a pointer to the start of the raw data
                uint16_t* raw_data_ptr = (uint16_t*)decoder_->get_image_data_start(current_super_frame_buffer_);
                // Calculate the start of the built data, this should be past where the raw data is held
                uint16_t* built_data_ptr = raw_data_ptr + (16 * 16 * 1000);

                // LOG4CXX_INFO(logger_, "Frame information:");
                // LOG4CXX_INFO(logger_, "current_super_frame_buffer_: " << current_super_frame_buffer_);
                // LOG4CXX_INFO(logger_, "get_image_data_start: " << (uint16_t*) decoder_->get_image_data_start(current_super_frame_buffer_));
                // LOG4CXX_INFO(logger_, "raw_data_ptr: " << raw_data_ptr);
                // LOG4CXX_INFO(logger_, "built_data_ptr: " << built_data_ptr);
                // LOG4CXX_INFO(logger_, "raw_data_ptr - current_super_frame_buffer_: " << raw_data_ptr - (uint16_t*) current_super_frame_buffer_);
                // LOG4CXX_INFO(logger_, "built_data_ptr - current_super_frame_buffer_: " << built_data_ptr - (uint16_t*) current_super_frame_buffer_);
                // LOG4CXX_INFO(logger_, "get_image_data_start - current_super_frame_buffer_: " << decoder_->get_image_data_start(current_super_frame_buffer_) - (char*) current_super_frame_buffer_);
                // LOG4CXX_INFO(logger_, "get_frame_buffer_size " << decoder_->get_frame_buffer_size());


                uint64_t frame_number = decoder_->get_super_frame_number(current_super_frame_buffer_);
                last_Frame = frame_number;

                decoder_->set_super_frame_image_size(current_super_frame_buffer_, frame_size);

                // Create new frame metadata object
                FrameMetaData frame_meta;
                frame_meta.set_dataset_name("raw");
                frame_meta.set_frame_number(frame_number);
                frame_meta.set_dimensions(dims);
                frame_meta.set_data_type(decoder_->get_frame_bit_depth());

                // Get the image size, with this we can work out if the frame has been compressed
                uint64_t image_size = decoder_->get_super_frame_image_size(current_super_frame_buffer_);

                frame_meta.set_compression_type(blosc);
                frame_meta.set_compression_type(no_compression);


                // Create the shared boost pointer to allow the plugin chain to access huge pages
                boost::shared_ptr<Frame> complete_frame =
                        boost::shared_ptr<Frame>(new DpdkSharedBufferFrame(
                                                    frame_meta, current_super_frame_buffer_,
                                                    decoder_->get_frame_buffer_size(),
                                                    nullptr, data_pointer_offset));

                complete_frame->set_image_size(decoder_->get_frame_data_size() * decoder_->get_frame_outer_chunk_size());
                complete_frame->set_outer_chunk_size(decoder_->get_frame_outer_chunk_size());


                // LOG4CXX_INFO(logger_, "Core " << lcore_id_ << ": Wrapping raw frame data...");
                    
                frame_callback_(complete_frame);



                //decoder_->set_super_frame_image_size(built_frame_buffer, frame_size);

                // Create new frame metadata object
                FrameMetaData built_frame_meta;
                built_frame_meta.set_dataset_name("built");
                built_frame_meta.set_frame_number(frame_number);
                built_frame_meta.set_dimensions(dims);
                built_frame_meta.set_data_type(decoder_->get_frame_bit_depth());

                // Get the image size, with this we can work out if the frame has been compressed
                uint64_t built_image_size = decoder_->get_super_frame_image_size(current_super_frame_buffer_);

                built_frame_meta.set_compression_type(blosc);
                built_frame_meta.set_compression_type(no_compression);


                // Create the shared boost pointer to allow the plugin chain to access huge pages
                boost::shared_ptr<Frame> built_complete_frame =
                        boost::shared_ptr<Frame>(new DpdkSharedBufferFrame(
                                                    built_frame_meta, current_super_frame_buffer_,
                                                    decoder_->get_frame_buffer_size(),
                                                    clear_frames_ring_, data_pointer_offset + 512000)
                                                );

                built_complete_frame->set_image_size(decoder_->get_frame_data_size() * decoder_->get_frame_outer_chunk_size());
                built_complete_frame->set_outer_chunk_size(decoder_->get_frame_outer_chunk_size());

                
                // LOG4CXX_INFO(logger_, "Core " << lcore_id_ << ": Wrapping built frame data...");
                frame_callback_(built_complete_frame);

                // Calculate status
                uint64_t cycles_spent = rte_get_tsc_cycles() - start_frame_cycles;
                total_frame_cycles += cycles_spent;
                cycles_working += cycles_spent;
                
                if (maximum_frame_cycles < cycles_spent)
                {
                    maximum_frame_cycles = cycles_spent;
                }
                

                frames_per_second++;
                processed_frames_++;
            }
        }

        LOG4CXX_INFO(logger_, "Core " << lcore_id_ << " completed");

        return true;
    }

    void BabydFrameWrapperCore::stop(void)
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

    void BabydFrameWrapperCore::status(OdinData::IpcMessage& status, const std::string& path)
    {
        LOG4CXX_DEBUG(logger_, "Status requested for BabydFrameWrapperCore_" << proc_idx_
            << " from the DPDK plugin");

        std::string status_path = path + "/BabydFrameWrapperCore_" + std::to_string(proc_idx_) + "/";

        // Create path for updstream ring status
        std::string ring_status = status_path + "upstream_rings/";

        // Create path for timing status
        std::string timing_status = status_path + "timing/";

        // Frame status reporting
        status.set_param(status_path + "frames_processes", processed_frames_);
        status.set_param(status_path + "frames_processed_per_second", processed_frames_hz_);
        status.set_param(status_path + "idle_loops", idle_loops_);
        status.set_param(status_path + "core_usage", (int)core_usage_);
        status.set_param(status_path + "last_frame_number", last_frame_);

        // Core timing status reporting
        status.set_param(timing_status + "mean_frame_us", mean_us_on_frame_);
        status.set_param(timing_status + "max_frame_us", maximum_us_on_frame_);

        // Upstream ring status
        status.set_param(ring_status + ring_name_str(config_.upstream_core, socket_id_, proc_idx_) + "_count", rte_ring_count(upstream_ring_));
        status.set_param(ring_status + ring_name_str(config_.upstream_core, socket_id_, proc_idx_) + "_size", rte_ring_get_size(upstream_ring_));

        status.set_param(ring_status + ring_name_clear_frames(socket_id_) + "_count" , rte_ring_count(clear_frames_ring_));
        status.set_param(ring_status + ring_name_clear_frames(socket_id_) + "_size" , rte_ring_get_size(clear_frames_ring_));
    }

    bool BabydFrameWrapperCore::connect(void)
    {

        // connect to the ring for incoming packets
        std::string upstream_ring_name = ring_name_str(config_.upstream_core, socket_id_, proc_idx_);
        struct rte_ring* upstream_ring = rte_ring_lookup(upstream_ring_name.c_str());
        if (upstream_ring == NULL)
        {
            // this needs to error out as there should always be upstream resources at this point
            LOG4CXX_INFO(logger_, config_.core_name << " : " << proc_idx_ << " Failed to Connect to upstream resources!");
            return false;
        }
        else
        {
            upstream_ring_ = upstream_ring;
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

    void BabydFrameWrapperCore::configure(OdinData::IpcMessage& config)
    {
        // Update the config based from the passed IPCmessage

        LOG4CXX_INFO(logger_, config_.core_name << " : " << proc_idx_ << " Got update config.");

    }

    DPDKREGISTER(DpdkWorkerCore, BabydFrameWrapperCore, "BabydFrameWrapperCore");
}
