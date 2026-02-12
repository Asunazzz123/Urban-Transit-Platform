#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "DBManager.h"

namespace py = pybind11;

class BaseNode {
protected:
	DBManager db_;

public:
	explicit BaseNode(const std::string& path)
		: db_(path) {}

	virtual ~BaseNode() = default;
};

/* ================= Input ================= */

class InputModule : public BaseNode {
public:
	using BaseNode::BaseNode;

	int insert_Station(const Station& data) { return db_.insert_Station(data); }
	int insert_Line(const Line& data) { return db_.insert_Line(data); }
	int insert_StationLine(const StationLine& data) { return db_.insert_StationLine(data); }
	int insert_TravelEdge(const TravelEdge& data) { return db_.insert_TravelEdge(data); }
	int insert_TransferEdge(const TransferEdge& data) { return db_.insert_TransferEdge(data); }
};

class OutputModule : public BaseNode {
public:
	using BaseNode::BaseNode;

	std::vector<Station> get_Stations() { return db_.get_Stations(); }
	std::vector<Line> get_Lines() { return db_.get_Lines(); }
	std::vector<StationLine> get_StationLines() { return db_.get_StationLines(); }
	std::vector<TravelEdge> get_TravelEdges() { return db_.get_TravelEdges(); }
	std::vector<TransferEdge> get_TransferEdges() { return db_.get_TransferEdges(); }
};


PYBIND11_MODULE(DBManager, m)
{
	m.doc() = "Sqlite DBManage Module,including Input and Output classes";

	py::class_<Station>(m, "Station")
		.def(py::init<>())
		.def_readwrite("city_name", &Station::city_name)
		.def_readwrite("station_id", &Station::station_id)
		.def_readwrite("name", &Station::name);

	py::class_<Line>(m, "Line")
		.def(py::init<>())
		.def_readwrite("city_name", &Line::city_name)
		.def_readwrite("line_id", &Line::line_id)
		.def_readwrite("name", &Line::name);

	py::class_<StationLine>(m, "StationLine")
		.def(py::init<>())
		.def_readwrite("city_name", &StationLine::city_name)
		.def_readwrite("station_line_id", &StationLine::station_line_id)
		.def_readwrite("station_id", &StationLine::station_id)
		.def_readwrite("line_id", &StationLine::line_id);

	py::class_<TravelEdge>(m, "TravelEdge")
		.def(py::init<>())
		.def_readwrite("city_name", &TravelEdge::city_name)
		.def_readwrite("from_station_line_id", &TravelEdge::from_station_line_id)
		.def_readwrite("to_station_line_id", &TravelEdge::to_station_line_id)
		.def_readwrite("travel_time", &TravelEdge::travel_time);

	py::class_<TransferEdge>(m, "TransferEdge")
		.def(py::init<>())
		.def_readwrite("city_name", &TransferEdge::city_name)
		.def_readwrite("from_station_line_id", &TransferEdge::from_station_line_id)
		.def_readwrite("to_station_line_id", &TransferEdge::to_station_line_id)
		.def_readwrite("transfer_time", &TransferEdge::transfer_time);

	py::class_<InputModule>(m,"InputModule",R"pbdoc(
		InputModule class for inserting data into the database
		)pbdoc")

		.def(py::init<const std::string&>())
		.def("insert_Station", &InputModule::insert_Station)
		.def("insert_Line", &InputModule::insert_Line)
		.def("insert_StationLine", &InputModule::insert_StationLine)
		.def("insert_TravelEdge", &InputModule::insert_TravelEdge)
		.def("insert_TransferEdge", &InputModule::insert_TransferEdge);

	py::class_<OutputModule>(m,"OutputModule",R"pbdoc(
		OutputModule class for retrieving data from the database
		)pbdoc")
		.def(py::init<const std::string&>())
		.def("get_Stations", &OutputModule::get_Stations)
		.def("get_Lines", &OutputModule::get_Lines)
		.def("get_StationLines", &OutputModule::get_StationLines)
		.def("get_TravelEdges", &OutputModule::get_TravelEdges)
		.def("get_TransferEdges", &OutputModule::get_TransferEdges);
}
