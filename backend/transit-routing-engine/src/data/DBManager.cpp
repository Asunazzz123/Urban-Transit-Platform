//DBManager.cpp
#include "DBManager.h"


DBManager::DBManager(const std::string& path)
{
    int status = sqlite3_open(path.c_str(), &db);
    if (status != SQLITE_OK) {
        std::string errMsg = db ? sqlite3_errmsg(db) : "Failed to open DB";
        if (db) sqlite3_close(db);
        throw std::runtime_error(errMsg);
    }
}

DBManager::~DBManager()
{
    if (db) {
        sqlite3_close(db);
        db = nullptr;
    }
}

int DBManager::insert_Station(const Station& data)
{
    if (!db) return -1;


    const char* sql = "INSERT INTO STATIONS (CITY_NAME,STATION_ID, STATION_NAME) VALUES (?, ?, ?);";
    sqlite3_stmt* stmt;

    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Prepare Error: " << sqlite3_errmsg(db) << std::endl;
        return -1;
    }
    sqlite3_bind_text(stmt, 1, data.city_name.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 2, data.station_id);
    sqlite3_bind_text(stmt, 3, data.name.c_str(), -1, SQLITE_TRANSIENT);

    int result = 0;
    if (sqlite3_step(stmt) != SQLITE_DONE) {
        std::cerr << "Insert Error: " << sqlite3_errmsg(db) << std::endl;
        result = 2;
    }

    sqlite3_finalize(stmt);
    return result;
}

int DBManager::insert_Line(const Line& data)
{
    if (!db) return -1;

    const char* sql = "INSERT INTO LINES (CITY_NAME,LINE_ID, LINE_NAME) VALUES (?,?, ?);";
    sqlite3_stmt* stmt;

    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Prepare Error: " << sqlite3_errmsg(db) << std::endl;
        return -1;
    }
    sqlite3_bind_text(stmt, 1, data.city_name.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 2, data.line_id);
    sqlite3_bind_text(stmt, 3, data.name.c_str(), -1, SQLITE_TRANSIENT);

    int result = 0;
    if (sqlite3_step(stmt) != SQLITE_DONE) {
        std::cerr << "Insert Error: " << sqlite3_errmsg(db) << std::endl;
        result = 2;
    }

    sqlite3_finalize(stmt);
    return result;
}

int DBManager::insert_StationLine(const StationLine& data)
{
    if (!db) return -1;

    const char* sql = "INSERT INTO STATION_LINE (CITY_NAME,STATION_LINE_ID, STATION_ID ,LINE_ID) VALUES (?,?, ?, ?);";
    sqlite3_stmt* stmt;

    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Prepare Error: " << sqlite3_errmsg(db) << std::endl;
        return -1;
    }

    sqlite3_bind_text(stmt, 1, data.city_name.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 2, data.station_line_id);
    sqlite3_bind_int(stmt, 3, data.station_id);
    sqlite3_bind_int(stmt, 4, data.line_id);
    int result = 0;
    if (sqlite3_step(stmt) != SQLITE_DONE) {
        std::cerr << "Insert Error: " << sqlite3_errmsg(db) << std::endl;
        result = 2;
    }

    sqlite3_finalize(stmt);
    return result;
}

int DBManager::insert_TravelEdge(const TravelEdge& data)
{
    if (!db) return -1;


    const char* sql = "INSERT INTO TRAVELEDGES (FROM_STATION, TO_STATION, TRAVEL_TIME) VALUES (?, ?, ?);";
    sqlite3_stmt* stmt;

    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Prepare Error: " << sqlite3_errmsg(db) << std::endl;
        return -1;
    }
    
    sqlite3_bind_int(stmt, 1, data.from_station_line_id);
    sqlite3_bind_int(stmt, 2, data.to_station_line_id);
    sqlite3_bind_int(stmt, 3, data.travel_time);
    int result = 0;
    if (sqlite3_step(stmt) != SQLITE_DONE) {
        std::cerr << "Insert Error: " << sqlite3_errmsg(db) << std::endl;
        result = 2;
    }

    sqlite3_finalize(stmt);
    return result;
}

int DBManager::insert_TransferEdge(const TransferEdge& data)
{
    if (!db) return -1;

    const char* sql = "INSERT INTO TRANSFEREDGES (FROM_STATION, TO_STATION, TRANSFER_TIME) VALUES (?, ?, ?);";
    sqlite3_stmt* stmt;
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Prepare Error: " << sqlite3_errmsg(db) << std::endl;
        return -1;
    }

    sqlite3_bind_int(stmt, 1, data.from_station_line_id);
    sqlite3_bind_int(stmt, 2, data.to_station_line_id);
    sqlite3_bind_int(stmt, 3, data.transfer_time);
    int result = 0;
    if (sqlite3_step(stmt) != SQLITE_DONE) {
        std::cerr << "Insert Error: " << sqlite3_errmsg(db) << std::endl;
        result = 2;
    }

    sqlite3_finalize(stmt);
    return result;
}
//数据读取
std::vector<Station> DBManager::get_Stations()
{
    std::vector<Station> results;
    if (!db) return results; 

    const char* sql = "SELECT STATION_ID, STATION_NAME FROM STATIONS;";
    sqlite3_stmt* stmt;

    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Query Error: " << sqlite3_errmsg(db) << std::endl;
        return results;
    }

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        Station s;


        s.station_id = sqlite3_column_int(stmt, 0);

        const unsigned char* text = sqlite3_column_text(stmt, 1);
        if (text) {
            s.name = reinterpret_cast<const char*>(text);
        }

        results.push_back(s);
    }


    sqlite3_finalize(stmt);

    return results;
}

std::vector<Line> DBManager::get_Lines()
{
    std::vector<Line> results;
    if (!db) return results;


    const char* sql = "SELECT LINE_ID, LINE_NAME FROM LINES;";
    sqlite3_stmt* stmt;

    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) != SQLITE_OK) {
        std::cerr << "Query Error: " << sqlite3_errmsg(db) << std::endl;
        return results;
    }

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        Line e;

        e.line_id = sqlite3_column_int(stmt, 0); 
        const unsigned char* text = sqlite3_column_text(stmt, 1);
        if (text) {
            e.name = reinterpret_cast<const char*>(text);
        }
        results.push_back(e);
    }

    sqlite3_finalize(stmt);
    return results;
}

std::vector<StationLine> DBManager::get_StationLines()
{
    std::vector<StationLine> result;
    const char* sql = "SELECT STATION_LINE_ID, STATION_ID, LINE_ID FROM STATION_LINE;";

    sqlite3_stmt* stmt = nullptr;

    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK)
    {
        throw std::runtime_error(sqlite3_errmsg(db));
    }

    while ((rc = sqlite3_step(stmt)) == SQLITE_ROW)
    {
        StationLine sl;
        sl.station_line_id = sqlite3_column_int(stmt, 0);
        sl.station_id = sqlite3_column_int(stmt, 1);
        sl.line_id = sqlite3_column_int(stmt, 2);

        result.push_back(sl);
    }
    if (rc != SQLITE_DONE)
    {
        sqlite3_finalize(stmt);
        throw std::runtime_error(sqlite3_errmsg(db));
    }

    sqlite3_finalize(stmt);
    return result;
}

std::vector<TravelEdge> DBManager::get_TravelEdges()
{
    std::vector<TravelEdge> result;

    const char* sql =
        "SELECT FROM_STATION, TO_STATION, TRAVEL_TIME FROM TRAVELEDGES;";

    sqlite3_stmt* stmt = nullptr;

    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        throw std::runtime_error(sqlite3_errmsg(db));
    }

    while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
        TravelEdge e;
        e.from_station_line_id = sqlite3_column_int(stmt, 0);
        e.to_station_line_id = sqlite3_column_int(stmt, 1);
        e.travel_time = sqlite3_column_int(stmt, 2);

        result.push_back(e);
    }

    if (rc != SQLITE_DONE) {
        sqlite3_finalize(stmt);
        throw std::runtime_error(sqlite3_errmsg(db));
    }

    sqlite3_finalize(stmt);
    return result;
}


std::vector<TransferEdge> DBManager::get_TransferEdges()
{
    std::vector<TransferEdge> result;

    const char* sql =
        "SELECT FROM_STATION, TO_STATION, TRANSFER_TIME FROM TRANSFEREDGES;";

    sqlite3_stmt* stmt = nullptr;

    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        throw std::runtime_error(sqlite3_errmsg(db));
    }

    while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
        TransferEdge e;
        e.from_station_line_id = sqlite3_column_int(stmt, 0);
        e.to_station_line_id = sqlite3_column_int(stmt, 1);
        e.transfer_time = sqlite3_column_int(stmt, 2);

        result.push_back(e);
    }

    if (rc != SQLITE_DONE) {
        sqlite3_finalize(stmt);
        throw std::runtime_error(sqlite3_errmsg(db));
    }

    sqlite3_finalize(stmt);
    return result;
}
