#include <pybind11/pybind11.h>
#include "image_tools.h"

namespace py = pybind11;

PYBIND11_MODULE(QtTools, m) {
    m.def("flood_fill", &floodFill);
    m.def("erase_area", &eraseArea);
    m.def("draw_icon", &drawIcon);
    m.def("recolor_icon", &recolorIcon);
}
