#ifndef CORE_SCENE_H
#define CORE_SCENE_H

#include "core/config.h"
#include "CGAL/Exact_predicates_exact_constructions_kernel.h"
#include "CGAL/Polyhedron_3.h"
#include "CGAL/Surface_mesh.h"
#include "CGAL/Nef_polyhedron_3.h"
#include "CGAL/boost/graph/convert_nef_polyhedron_to_polygon_mesh.h"
#include "CGAL/IO/Nef_polyhedron_iostream_3.h"

typedef CGAL::Exact_predicates_exact_constructions_kernel Exact_kernel;
typedef CGAL::Polyhedron_3<Exact_kernel> Polyhedron;
typedef CGAL::Surface_mesh<Exact_kernel::Point_3> Surface_mesh;
typedef CGAL::Nef_polyhedron_3<Exact_kernel> Nef_polyhedron;

class Scene {
public:
    Scene();

    void LoadScene(const std::string& file_name);
    void SaveScene(const std::string& file_name);

private:
    Nef_polyhedron objects_;
};

#endif