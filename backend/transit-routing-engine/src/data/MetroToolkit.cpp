#include "MetroToolkit.h"

#include <queue>
#include <stdexcept>
#include <functional>

// =======================
// 构造 & 初始化
// =======================

MetroToolkit::MetroToolkit(DBManager& db_)
    : db(db_)
{
    // 预加载 name -> id
    for (const auto& s : db.getStations()) {
        stationNameToId[s.name] = s.station_id;
    }

    for (const auto& l : db.getLines()) {
        lineNameToId[l.name] = l.line_id;
    }

    buildGraph();
}

// =======================
// 构建多层图
// =======================

void MetroToolkit::buildGraph()
{
    const auto stationLines = db.getStationLines();
    const auto travelEdges = db.getTravelEdges();
    const auto transferEdges = db.getTransferEdges();

    // 1. 创建 node
    for (const auto& sl : stationLines) {
        int node_id = static_cast<int>(nodes.size());
        nodes.push_back({ sl.station_id, sl.line_id });
        stationLineIdToNode[sl.station_line_id] = node_id;
    }

    graph.resize(nodes.size());

    // 2. 加运行边
    for (const auto& e : travelEdges) {
        int u = stationLineIdToNode.at(e.from_station_line_id);
        int v = stationLineIdToNode.at(e.to_station_line_id);
        graph[u].push_back({ v, e.travel_time, false });
    }

    // 3. 加换乘边
    for (const auto& e : transferEdges) {
        int u = stationLineIdToNode.at(e.from_station_line_id);
        int v = stationLineIdToNode.at(e.to_station_line_id);
        graph[u].push_back({ v, e.transfer_time, true });
    }
}

// =======================
// 对外查询接口
// =======================

int MetroToolkit::queryTime(const std::string& from_station,
    const std::string& from_line,
    const std::string& to_station,
    const std::string& to_line)
{
    int start = getNodeIdByName(from_station, from_line);
    int target = getNodeIdByName(to_station, to_line);

    return dijkstra(start, target);
}

// =======================
// name -> node_id
// =======================

int MetroToolkit::getNodeIdByName(const std::string& station,
    const std::string& line) const
{
    auto s_it = stationNameToId.find(station);
    auto l_it = lineNameToId.find(line);

    if (s_it == stationNameToId.end() ||
        l_it == lineNameToId.end()) {
        throw std::runtime_error("Unknown station or line name");
    }

    int station_id = s_it->second;
    int line_id = l_it->second;

    for (size_t i = 0; i < nodes.size(); ++i) {
        if (nodes[i].station_id == station_id &&
            nodes[i].line_id == line_id) {
            return static_cast<int>(i);
        }
    }

    throw std::runtime_error("Station-line combination not found");
}

// =======================
// Dijkstra（核心复杂性）
// =======================

int MetroToolkit::dijkstra(int start, int target) const
{
    const int INF = std::numeric_limits<int>::max();
    std::vector<int> dist(nodes.size(), INF);

    using State = std::pair<int, int>; // (dist, node)
    std::priority_queue<State, std::vector<State>, std::greater<>> pq;

    dist[start] = 0;
    pq.push({ 0, start });

    while (!pq.empty()) {
        auto [cur_dist, u] = pq.top();
        pq.pop();

        if (u == target) {
            return cur_dist;
        }

        if (cur_dist > dist[u]) continue;

        for (const auto& e : graph[u]) {
            int v = e.to;
            int nd = cur_dist + e.weight;

            if (nd < dist[v]) {
                dist[v] = nd;
                pq.push({ nd, v });
            }
        }
    }

    return -1; 
}

int MetroToolkit::queryTimeWithTransferPenalty(
    const std::string& from_station,
    const std::string& from_line,
    const std::string& to_station,
    const std::string& to_line,
    int transfer_penalty)
{
    int start = getNodeIdByName(from_station, from_line);
    int target = getNodeIdByName(to_station, to_line);

    const int INF = std::numeric_limits<int>::max();
    std::vector<int> dist(nodes.size(), INF);

    using State = std::pair<int, int>; // (dist, node)
    std::priority_queue<State, std::vector<State>, std::greater<>> pq;

    dist[start] = 0;
    pq.push({ 0, start });

    while (!pq.empty()) {
        auto [cur_dist, u] = pq.top();
        pq.pop();

        if (u == target) {
            return cur_dist;
        }

        if (cur_dist > dist[u]) continue;

        for (const auto& e : graph[u]) {
            int v = e.to;

            int cost = e.weight;
            if (e.is_transfer) {
                cost += transfer_penalty;
            }

            int nd = cur_dist + cost;

            if (nd < dist[v]) {
                dist[v] = nd;
                pq.push({ nd, v });
            }
        }
    }

    return -1;
}
