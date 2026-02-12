#pragma once

#include <vector>
#include <unordered_map>
#include <string>
#include <limits>

#include "DBManager.h"


class MetroToolkit {
public:
    explicit MetroToolkit(DBManager& db);

    // 查询接口（对外用）
    int queryTime(
        const std::string& from_station,
        const std::string& from_line,
        const std::string& to_station,
        const std::string& to_line);

    int queryTimeWithTransferPenalty(
        const std::string& from_station,
        const std::string& from_line,
        const std::string& to_station,
        const std::string& to_line,
        int transfer_penalty);
private:
    // ===== 内部图结构 =====
    struct Node {
        int station_id;
        int line_id;
    };

    struct Edge {
        int to;
        int weight; 
        bool is_transfer;
    };

    // ===== 核心构建 =====
    void buildGraph();

    // ===== 搜索 =====
    int dijkstra(int start, int target) const;

    // ===== 工具函数 =====
    int getNodeIdByName(const std::string& station,
        const std::string& line) const;

private:
    DBManager& db;

    // node_id -> Node
    std::vector<Node> nodes;

    // node_id -> edges
    std::vector<std::vector<Edge>> graph;

    // station_line_id -> node_id
    std::unordered_map<int, int> stationLineIdToNode;

    // name -> id 映射（查找加速）
    std::unordered_map<std::string, int> stationNameToId;
    std::unordered_map<std::string, int> lineNameToId;
};
