#include <array>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

struct Particle { double x, y, vx = 0, vy = 0; };

int main(int argc, char** argv) {
  const std::string output = argc > 1 ? argv[1] : "particles.csv";
  std::mt19937 generator(7);
  std::uniform_real_distribution<double> jitter(-.08, .08);
  std::vector<Particle> particles(96);
  for (auto& p : particles) { p.x = .5 + jitter(generator); p.y = .72 + jitter(generator); }
  std::ofstream file(output); file << "frame,id,x,y\n";
  for (int frame = 0; frame < 90; ++frame) {
    for (std::size_t i = 0; i < particles.size(); ++i) {
      auto& p = particles[i]; p.vy -= 1.8 * .016; p.x += p.vx * .016; p.y += p.vy * .016;
      if (p.y < .05) { p.y = .05; p.vy *= -.25; }
      file << frame << ',' << i << ',' << p.x << ',' << p.y << '\n';
    }
  }
  std::cout << "Ballistic starter only: implement P2G/G2P, stress, plasticity, and collisions.\n";
}
