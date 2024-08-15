
typedef uint64_t _ADXDMA_UINT64;
typedef uint32_t _ADXDMA_UINT32;
typedef uint16_t _ADXDMA_UINT16;
typedef uint8_t  _ADXDMA_UINT8;
typedef int      _ADXDMA_BOOL;

typedef int ADXDMA_HDEVICE;
typedef int ADXDMA_HDMA;
typedef int ADXDMA_HWINDOW;

/*
** Status and error codes
*/
typedef enum _ADXDMA_STATUS
{
    /* Operation completed without error. */
    ADXDMA_SUCCESS                 = 0x0,

    /* Asynchronous operation started without error. */
    ADXDMA_STARTED                 = 0x1,

    /* Operation transferred some, but not all of the requested bytes. */
    ADXDMA_TRUNCATED               = 0x2,

    /* An error in the API logic was detected */
    ADXDMA_INTERNAL_ERROR          = 0x100,

    /* An unexpected error caused the operation to fail */
    ADXDMA_UNEXPECTED_ERROR        = 0x101,

    /* The driver might not be correctly installed */
    ADXDMA_BAD_DRIVER              = 0x102,

    /* Couldn't allocate memory required to complete operation */
    ADXDMA_NO_MEMORY               = 0x103,

    /* The calling process does not have permission to perform the operation */
    ADXDMA_ACCESS_DENIED           = 0x104,

    /* Failed to open the device with the specified index */
    ADXDMA_DEVICE_NOT_FOUND        = 0x105,

    /* The operation was aborted due to software-requested cancellation */
    ADXDMA_CANCELLED               = 0x106,

    /* The operation failed due to an error in the hardware */
    ADXDMA_HARDWARE_ERROR          = 0x107,

    /* The operation was aborted the hardware being reset */
    ADXDMA_HARDWARE_RESET          = 0x108,

    /* The operation was aborted due to a hardware power-down event */
    ADXDMA_HARDWARE_POWER_DOWN     = 0x109,

    /* The primary parameter to the function was invalid */
    ADXDMA_INVALID_PARAMETER       = 0x10A,

    /* A flag was invalid or not recognized */
    ADXDMA_INVALID_FLAG            = 0x10B,

    /* The device handle was invalid */
    ADXDMA_INVALID_HANDLE          = 0x10C,

    /* The index parameter was invalid */
    ADXDMA_INVALID_INDEX           = 0x10D,

    /* A NULL pointer was passed where non-NULL was required */
    ADXDMA_NULL_POINTER            = 0x10E,

    /* The hardware or the ADXDMA driver does not support the requested operation */
    ADXDMA_NOT_SUPPORTED           = 0x10F,

    /* The wrong kind of handle was supplied for an API function (e.g. a Window handle passed instead of a Device handle, or vice versa) */
    ADXDMA_WRONG_HANDLE_TYPE       = 0x110,

    /* The user-supplied timeout value was exceeded */
    ADXDMA_TIMEOUT_EXPIRED         = 0x111,

    /* At least one bit in the sensitivity parameter refers to a non-existent User Interrupt */
    ADXDMA_INVALID_SENSITIVITY     = 0x112,

    /* The virtual base address to be unmapped from the process' address space was not recognized */
    ADXDMA_INVALID_MAPPING         = 0x113,

    /* The word size specified was not valid */
    ADXDMA_INVALID_WORD_SIZE       = 0x114,

    /* The requested region was partially or completely out of bounds */
    ADXDMA_INVALID_REGION          = 0x115,

    /* The requested region exceeded a system-imposed limit */
    ADXDMA_REGION_OS_LIMIT         = 0x116,

    /* The limit on the number of locked buffers has been reached */
    ADXDMA_LOCK_LIMIT              = 0x117,

    /* An invalid locked buffer handle was supplied */
    ADXDMA_INVALID_BUFFER_HANDLE   = 0x118,

    /* Attempt to unlock a buffer owned by a different device handle */
    ADXDMA_NOT_BUFFER_OWNER        = 0x119,

    /* Attempt to change DMA queue configuration when it was not idle */
    ADXDMA_DMAQ_NOT_IDLE           = 0x11A,

    /* Invalid DMA Queue mode requested */
    ADXDMA_INVALID_DMAQ_MODE       = 0x11B,

    /* Maximum outstanding DMA transfer count reached */
    ADXDMA_DMAQ_OUTSTANDING_LIMIT  = 0x11C,

    /* Invalid address alignment, or length is not an integer multiple of length granularity */
    ADXDMA_INVALID_DMA_ALIGNMENT   = 0x11D,

    /* At least one Window mapping exists, preventing safe reset */
    ADXDMA_EXISTING_MAPPING        = 0x11E,

    /* Currently not used */
    ADXDMA_ALREADY_CANCELLING      = 0x11F,

    /* Attempting to perform an operation while there is already one in progress */
    ADXDMA_DEVICE_BUSY             = 0x120,

    /* Attempting to join a non-existent operation */
    ADXDMA_DEVICE_IDLE             = 0x121,

    /* At least one DMA descriptor was closed early by C2H user logic asserting TLAST */
    ADXDMA_C2H_TLAST_ASSERTED      = 0x122,

    ADXDMA_STATUS_FORCE32BITS = 0x7FFFFFFF
} ADXDMA_STATUS;

typedef struct _ADXDMA_PCI_ID {
  _ADXDMA_UINT16 Vendor;
  _ADXDMA_UINT16 Device;
  _ADXDMA_UINT16 SubsystemVendor;
  _ADXDMA_UINT16 SubsystemDevice;
  _ADXDMA_UINT8  Revision;
  _ADXDMA_UINT8  ClassMajor;
  _ADXDMA_UINT8  ClassMinor;
  _ADXDMA_UINT8  ProgrammingInterface;
} ADXDMA_PCI_ID;

typedef struct _ADXDMA_PCI_LOCATION {
  _ADXDMA_UINT16 Domain;
  _ADXDMA_UINT8  Bus;
  _ADXDMA_UINT8  Slot;
  _ADXDMA_UINT8  Function;
} ADXDMA_PCI_LOCATION;

typedef struct _ADXDMA_DEVICE_INFO {
  unsigned int        NumWindow;
  unsigned int        ControlWindowIndex;
  unsigned int        NumH2C;
  unsigned int        NumC2H;
  unsigned int        NumUserInterrupt;
  unsigned int        NumMSIVector;
  ADXDMA_PCI_ID       HardwareID;
  ADXDMA_PCI_LOCATION Location;
} ADXDMA_DEVICE_INFO;

typedef struct _ADXDMA_API_INFO {
  /* <adxdma.h> version against which the API library binary was built */
  struct {
    _ADXDMA_UINT16 Super;
    _ADXDMA_UINT16 Major;
    _ADXDMA_UINT16 Minor;
  } HeaderVersion;
  /* API library binary version */
  struct {
    _ADXDMA_UINT16 Major;
    _ADXDMA_UINT16 Minor;
    _ADXDMA_UINT16 Bugfix;
  } BinaryVersion;
} ADXDMA_API_INFO;

typedef struct _ADXDMA_DMA_ENGINE_INFO {
  _ADXDMA_BOOL       IsH2C;
  _ADXDMA_BOOL       IsStream;
  unsigned int       Index;
  unsigned int       AddressAlignment;
  unsigned int       LengthGranularity;
  unsigned int       AddressBits;
} ADXDMA_DMA_ENGINE_INFO;

typedef struct _ADXDMA_DRIVER_INFO {
  /* <adxdma.h> version against which the Kernel-mode driver binary was built */
  struct {
    _ADXDMA_UINT16 Super;
    _ADXDMA_UINT16 Major;
    _ADXDMA_UINT16 Minor;
  } HeaderVersion;
  /* Kernel-mode driver binary version */
  struct {
    _ADXDMA_UINT16 Major;
    _ADXDMA_UINT16 Minor;
    _ADXDMA_UINT16 Bugfix;
  } BinaryVersion;
} ADXDMA_DRIVER_INFO;

typedef struct _ADXDMA_WINDOW_INFO {
  _ADXDMA_UINT64 BusSize;     /* Size of BAR in bytes on I/O bus (i.e. in PCIe memory space) */
  _ADXDMA_UINT64 BusBase;     /* Base address of BAR on I/O bus (i.e. in PCIe memory space) */
  _ADXDMA_UINT64 VirtualSize; /* Size of BAR when mapped into a process' virtual address space */
  _ADXDMA_UINT32 Flags;       /* See ADXDMA_WINDOW_* values in <adxdma/types.h> */
} ADXDMA_WINDOW_INFO;

typedef struct _ADXDMA_COMPLETION {
  size_t        Transferred; /* Number of bytes successfully transferred */
  ADXDMA_STATUS Reason;      /* Reason for not transferring all requested bytes */
} ADXDMA_COMPLETION;


ADXDMA_STATUS ADXDMA_Open(unsigned int deviceIndex, _ADXDMA_BOOL bPassive, ADXDMA_HDEVICE* phDevice);
ADXDMA_STATUS ADXDMA_OpenDMAEngine(ADXDMA_HDEVICE hParentDevice, unsigned int deviceIndex, _ADXDMA_BOOL bPassive,
                                   _ADXDMA_BOOL bOpenH2C, unsigned int engineIndex, ADXDMA_HDMA* phDMAEngine);
ADXDMA_STATUS ADXDMA_OpenWindow(ADXDMA_HDEVICE hParentDevice, unsigned int deviceIndex, _ADXDMA_BOOL bPassive,
                                unsigned int windowIndex, ADXDMA_HWINDOW* phWindow);

ADXDMA_STATUS ADXDMA_ReadDMA(ADXDMA_HDMA hDMAEngine, _ADXDMA_UINT32 flags, _ADXDMA_UINT64 remoteAddress,
                             void* pBuffer, size_t transferLength, ADXDMA_COMPLETION* pCompletionInfo);
ADXDMA_STATUS ADXDMA_ReadWindow(ADXDMA_HWINDOW hWindow, _ADXDMA_UINT32 flags, _ADXDMA_UINT8 preferredSize,
                                _ADXDMA_UINT64 offset, size_t length, void* pBuffer, ADXDMA_COMPLETION* pCompletionInfo);
ADXDMA_STATUS ADXDMA_WriteWindow(ADXDMA_HWINDOW hWindow, _ADXDMA_UINT32 flags, _ADXDMA_UINT8 preferredSize,
                                _ADXDMA_UINT64 offset, size_t length, const void* pBuffer, ADXDMA_COMPLETION* pCompletionInfo);

ADXDMA_STATUS ADXDMA_CloseDMAEngine(ADXDMA_HDMA hDMAEngine);
ADXDMA_STATUS ADXDMA_CloseWindow(ADXDMA_HWINDOW hWindow);
ADXDMA_STATUS ADXDMA_Close(ADXDMA_HDEVICE hDevice);


ADXDMA_STATUS ADXDMA_GetDriverInfo(ADXDMA_DRIVER_INFO* pDriverInfo);
ADXDMA_STATUS ADXDMA_GetDeviceInfo(ADXDMA_HDEVICE hDevice, ADXDMA_DEVICE_INFO* pDeviceInfo);
ADXDMA_STATUS ADXDMA_GetAPIInfo(ADXDMA_API_INFO* pAPIInfo);
ADXDMA_STATUS ADXDMA_GetDMAEngineInfo(ADXDMA_HDEVICE hDevice, _ADXDMA_BOOL bH2c,
                        unsigned int engineIndex, ADXDMA_DMA_ENGINE_INFO* pDMAEngineInfo);
ADXDMA_STATUS ADXDMA_GetWindowInfo(ADXDMA_HDEVICE hDevice, unsigned int windowIndex, ADXDMA_WINDOW_INFO* pWindowInfo);