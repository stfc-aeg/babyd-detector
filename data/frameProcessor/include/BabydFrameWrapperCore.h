#ifndef INCLUDE_BabydFrameWrapperCore_H_
#define INCLUDE_BabydFrameWrapperCore_H_

#include <log4cxx/logger.h>
using namespace log4cxx;
using namespace log4cxx::helpers;
#include <DebugLevelLogger.h>

#include "DpdkWorkerCore.h"
#include "DpdkCoreConfiguration.h"
#include "BabydFrameWrapperCoreConfiguration.h"
#include "ProtocolDecoder.h"
#include <rte_ring.h>
#include <blosc.h>
#include <rte_memcpy.h>

namespace FrameProcessor
{

    class BabydFrameWrapperCore : public DpdkWorkerCore
    {
    public:

        BabydFrameWrapperCore(
            int fb_idx, int socket_id, DpdkWorkCoreReferences &dpdkWorkCoreReferences
        );
        ~BabydFrameWrapperCore();

        bool run(unsigned int lcore_id);
        void stop(void);
        void status(OdinData::IpcMessage& status, const std::string& path);
        bool connect(void);
        void configure(OdinData::IpcMessage& config);

    private:
        int proc_idx_;
        ProtocolDecoder* decoder_;
        BabydFrameWrapperConfiguration config_;

        LoggerPtr logger_;
        FrameCallback& frame_callback_;

        uint64_t frames_wrapped_;
        uint64_t frames_wrapped_hz_;
        uint64_t idle_loops_;
        uint64_t avg_us_spent_wrapping_;

        struct rte_ring* frame_ready_ring_;
        struct rte_ring* clear_frames_ring_;
        struct rte_ring* upstream_ring_;
    };
}

#endif // INCLUDE_BabydFrameWrapperCore_H_