/*
 * BabydDetectorPlugin.h
 *
 *  Created on: 10 June 2022
 *      Author: Tim Nicholls, STFC Detector Systems Software Group
 */

#ifndef INCLUDE_BABYDDETECTORPLUGIN_H_
#define INCLUDE_BABYDDETECTORPLUGIN_H_

#include<string>
#include<map>

#include <boost/scoped_ptr.hpp>

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;

#include <DpdkFrameProcessorPlugin.h>
#include "BabydDetectorDecoder.h"
#include "BabydDetectorDefinitions.h"
#include "ClassLoader.h"


namespace FrameProcessor
{

  /** Babyd Detector Plugin
   *
   * The BabydDetectorPlugin class implements a DPDK-aware plugin capable of receiving data
   * frame packets from upstream DPDK packet processing cores and injecting them into the
   * frameProcessor frame data flow.
   */
  class BabydDetectorPlugin : public DpdkFrameProcessorPlugin
  {

  public:
    BabydDetectorPlugin();
    virtual ~BabydDetectorPlugin();

    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void requestConfiguration(OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);
    bool reset_statistics(void);

    void process_frame(boost::shared_ptr<Frame> frame);

  private:

    /** Pointer to logger **/
    LoggerPtr logger_;

    BabydDetectorDecoder decoder_;

  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, BabydDetectorPlugin, "BabydDetectorPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_BABYDDETECTORPLUGIN_H_ */
