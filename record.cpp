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
//       enter main
//       enter functionA()
//       enter functionB()
//       exit functionB()
//       ... etc ...

#include <cstdlib>
#include <dlfcn.h>
#include <stdio.h>

namespace {

static bool g_in_record = false;
static FILE *g_file;

__attribute__((constructor, no_instrument_function))
void constructor() {
  g_in_record = true;
  if (const char* record_cct = std::getenv("RECORD_CCT"))
    g_file = fopen(record_cct, "w");
  g_in_record = false;
}

__attribute__((destructor, no_instrument_function))
void destructor() {
  g_in_record = true;

  if (g_file)
    fclose(g_file);

  g_in_record = false;
}

__attribute__((no_instrument_function))
void record(void *dest, void *src, bool is_enter) {
  if (g_in_record || !g_file)
    return;

  g_in_record = true;

  // TODO(phil): Cache the dladdr call to reduce lookups (see:
  // https://michael.hinespot.com/tutorials/gcc_trace_functions).
  Dl_info dest_info;
  // TODO(phil): Add a buffer for better performance (see:
  // https://github.com/microsoft/ChakraCore/blob/master/lib/Runtime/PlatformAgnostic/Platform/Common/Trace.cpp).
  fprintf(g_file, "%s %s\n",
      is_enter ? "entering" : "exiting",
      dladdr(dest, &dest_info) ? dest_info.dli_sname : "?");
  fflush(g_file);

  g_in_record = false;
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
