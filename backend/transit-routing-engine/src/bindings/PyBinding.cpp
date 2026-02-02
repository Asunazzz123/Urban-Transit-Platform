#include <pybind11/pybind.h>
#include <pybind11/embed.h>
#include <iostream>
#include "DBManager.h"

namespace py = pybind11;
namespace db = DBManager;

class BaseNode {
protected:
	db::DBManager db_;

public:
	explicit BaseNode(const std::string& path)
		: db_(path) {}

	virtual ~BaseNode() = default;
};

/* ================= Input ================= */

class InputModule : public BaseNode {
public:
	using BaseNode::BaseNode;

	int insert_Station(const Station& data);
	int insert_Line(const Line& data);
	int insert_StationLine(const StationLine& data);
	int insert_TravelEdge(const TravelEdge& data);
	int insert_TransferEdge(const TransferEdge& data);
};

class OutputModule : public BaseNode {
public:
	using BaseNode::BaseNode;

	std::vector<Station> get_Stations();
	std::vector<Line> get_Lines();
	std::vector<StationLine> get_StationLines();
	std::vector<TravelEdge> get_TravelEdges();
	std::vector<TransferEdge> get_TransferEdges();
};


PYBIND11_MODULE(DBManager, m)
{
	m.doc() = "Sqlite DBManage Module,including Input and Output classes";
	py::class_<InputModule>
}

