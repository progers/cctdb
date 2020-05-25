// Helper utility to record all function calls.
// Compile the target executable with: -finstrument-functions record.o
// Run the target executable with: RECORD_CCT=recording.txt
//
// Example:
//   g++ -c record.cpp -o record.o
//   g++ -finstrument-functions record.o my_program.cpp -o my_program
//   RECORD_CCT=recording.txt ./my_program
//
//   recording.txt will look like:
//       [thread id] entering main
//       [thread id] entering functionA()
//       [thread id] entering functionB()
//       [thread id] exiting functionB()
//       ... etc ...

#include <dlfcn.h>
#include <fstream>
#include <mutex>
#include <thread>

namespace {

// True while in recording logic that should not be recorded.
static bool g_in_record = false;

static std::mutex mut;
static std::ofstream* g_file;

__attribute__((constructor, no_instrument_function))
void constructor() {
  g_in_record = true;
  // TODO(phil): Improve performance when RECORD_CCT is not specified.
  if (const char* filename = std::getenv("RECORD_CCT")) {
    g_file = new std::ofstream();
    g_file->open(filename);
  }
  g_in_record = false;
}

__attribute__((destructor, no_instrument_function))
void destructor() {
  g_in_record = true;
  if (g_file)
    g_file->close();
  g_in_record = false;
}

__attribute__((no_instrument_function))
void record(void *dest, void *src, bool is_enter) {
  // TODO(phil): Consider lock-free approach such as glog.
  std::lock_guard<std::mutex> lock(mut);
  if (!g_in_record && g_file) {
    g_in_record = true;

    // TODO(phil): Cache the dladdr call to reduce lookups (see:
    // https://michael.hinespot.com/tutorials/gcc_trace_functions).
    Dl_info dest_info;
    // TODO(phil): Add a buffer for better performance (see:
    // https://github.com/microsoft/ChakraCore/blob/master/lib/Runtime/PlatformAgnostic/Platform/Common/Trace.cpp).
    *g_file << "tid" <<  std::this_thread::get_id();
    *g_file << " " << (is_enter ? "entering" : "exiting");
    *g_file << " " << (dladdr(dest, &dest_info) ? dest_info.dli_sname : "?");
    *g_file << std::endl;

    g_in_record = false;
  }
}

}

extern "C" {
  __attribute__((no_instrument_function))
  extern void __cyg_profile_func_enter(void *dest, void *src) {
    record(dest, src, true);
  }
  __attribute__((no_instrument_function))
  extern void __cyg_profile_func_exit(void *dest, void *src) {
    record(dest, src, false);
  }
}
