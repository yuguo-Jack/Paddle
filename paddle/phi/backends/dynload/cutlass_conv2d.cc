/* Copyright (c) 2024 PaddlePaddle Authors. All Rights Reserved.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License. */

#include "paddle/phi/backends/dynload/cutlass_conv2d.h"
#include <string>
#include "paddle/phi/core/enforce.h"

namespace phi::dynload {

std::once_flag cutlass_dso_flag;
void* cutlass_dso_handle;

void* GetCutlassConv2dHandle() {
  std::string dso_name = "libCutlassConv2d.so";

  std::call_once(cutlass_dso_flag, [&]() {
#if !defined(_WIN32)
    int dynload_flags = RTLD_LAZY | RTLD_LOCAL;
#else
  int dynload_flags = 0;
#endif  // !_WIN32

    cutlass_dso_handle = dlopen(dso_name.c_str(), dynload_flags);

    PADDLE_ENFORCE_NOT_NULL(
        cutlass_dso_handle,
        phi::errors::NotFound(
            "libCutlassConv2d.so is needed, "
            "but libCutlassConv2d.so is not found.\n"
            "  Suggestions:\n"
            "  1. Refer paddle/phi/kernels/fusion/cutlass/conv2d/README.md, "
            "and compile this library.\n"
            "  2. Configure environment variables as "
            "follows:\n"
            "  - Linux: set LD_LIBRARY_PATH by `export LD_LIBRARY_PATH=...`\n"
            "  - Windows: set PATH by `set PATH=XXX;%PATH%`\n"
            "  - Mac: set  DYLD_LIBRARY_PATH by `export "
            "DYLD_LIBRARY_PATH=...`\n"));
  });

  return cutlass_dso_handle;
}

}  // namespace phi::dynload
