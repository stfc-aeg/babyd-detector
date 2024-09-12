/*
 * BabydPlugin.cpp
 *
 *  Created on: 10 September 2024
 *      Author: Dominic Banks, STFC Detector Systems Software Group
 */

#include "BabydPlugin.h"
#include "version.h"

namespace FrameProcessor
{

  /**
   * The constructor sets up logging used within the class.
   */
  BabydPlugin::BabydPlugin() :
    DpdkFrameProcessorPlugin()
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.BabydPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_INFO(logger_, "BabydPlugin version " << this->get_version_long() << " loaded");

  }

  /**
   * Destructor.
   */
  BabydPlugin::~BabydPlugin()
  {
    LOG4CXX_TRACE(logger_, "BabydPlugin destructor.");
  }

  /**
   * Configure the plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[out] reply - Reference to the reply IpcMessage object.
   */
  void BabydPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    LOG4CXX_INFO(logger_, "Configuring Babyd  plugin");

    LOG4CXX_INFO(logger_, "Plugin name: " << this->get_name());
    FrameCallback frame_callback = boost::bind(&BabydPlugin::process_frame, this, _1);

    DpdkFrameProcessorPlugin::configure(config, reply, &decoder_, frame_callback);

  }

  void BabydPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the plugin
    LOG4CXX_INFO(logger_, "Configuration requested for Babyd  plugin");

    DpdkFrameProcessorPlugin::requestConfiguration(reply);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
   */
  void BabydPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_INFO(logger_, "Status requested for Babyd  plugin");

    status.set_param(get_name() + "/" + "wibble", true);

    DpdkFrameProcessorPlugin::status(status);
  }

  /**
   * Reset process plugin statistics, i.e. counter of packets lost
   */
  bool BabydPlugin::reset_statistics(void)
  {
    LOG4CXX_INFO(logger_, "Statistics reset requested for Babyd  plugin")

    bool reset_ok = true;

    reset_ok &= DpdkFrameProcessorPlugin::reset_statistics();

    return reset_ok;
  }

  /**
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void BabydPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    // LOG4CXX_DEBUG(logger_, "Processing frame in Babyd  plugin");
    this->push(frame);
  }


} /* namespace FrameProcessor */

