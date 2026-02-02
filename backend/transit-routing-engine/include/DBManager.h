//DBManager.h
#pragma once
#include <iostream>
#include <string>
#include <vector>
#include <sqlite3.h>
#include <stdexcept>

// 车站表
struct Station {
	std::string city_name;
	int station_id;
	std::string name;
};

//线网表
struct Line {
	std::string city_name;
	int line_id;
	std::string name;
};

//车站-线网表
struct StationLine {
	std::string city_name;
	int station_line_id;
	int station_id;
	int line_id;
};

//运行用时表
struct TravelEdge {
	std::string city_name;
	int from_station_line_id;
	int to_station_line_id;
	int travel_time; 
};

//换乘用时表
struct TransferEdge
{
	std::string city_name;
	int from_station_line_id;
	int to_station_line_id;
	int transfer_time;
};
class DBManager 
{
private:
	sqlite3* db = nullptr;
public:
	explicit DBManager(const std::string& path);
	~DBManager();
	// 输入函数
	int insert_Station(const Station& data);
	int insert_Line(const Line& data);
	int insert_StationLine(const StationLine& data);
	int insert_TravelEdge(const TravelEdge& data);
	int insert_TransferEdge(const TransferEdge& data);
	// 输出函数
	std::vector<Station> get_Stations();
	std::vector<Line> get_Lines();
	std::vector<StationLine> get_StationLines();
	std::vector<TravelEdge> get_TravelEdges();
	std::vector<TransferEdge> get_TransferEdges();
};



