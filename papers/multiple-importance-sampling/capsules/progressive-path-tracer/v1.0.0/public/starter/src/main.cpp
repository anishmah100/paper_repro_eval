#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
  const std::string output = argc > 1 ? argv[1] : "progressive.ppm";
  constexpr int width = 480, height = 360;
  std::ofstream file(output, std::ios::binary);
  file << "P6\n" << width << " " << height << "\n255\n";
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      const double u = (x + 0.5) / width, v = (y + 0.5) / height;
      const double sphere = std::max(0.0, 1.0 - std::hypot(u - .5, v - .52) * 4.0);
      const unsigned char rgb[3] = {
        static_cast<unsigned char>(255 * (.05 + .8 * sphere)),
        static_cast<unsigned char>(255 * (.06 + .45 * sphere)),
        static_cast<unsigned char>(255 * (.09 + .2 * sphere))};
      file.write(reinterpret_cast<const char*>(rgb), 3);
    }
  }
  std::cout << "Starter preview only: implement transport, BSDF/light sampling, and MIS.\n";
}
