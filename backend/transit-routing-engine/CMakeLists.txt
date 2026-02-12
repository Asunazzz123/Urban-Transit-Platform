cmake_minimum_required(VERSION 3.14)

# 使用你的文件夹名称作为项目名
project(transit-routing-engine VERSION 1.0)

# ==========================================
# 1. C++ 标准 (C++17)
# ==========================================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ==========================================
# 2. 依赖查找 (SQLite3)
# ==========================================
include(FetchContent)

# 下载并编译 SQLite3
FetchContent_Declare(
    sqlite3
    URL https://www.sqlite.org/2024/sqlite-amalgamation-3450100.zip
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)

FetchContent_MakeAvailable(sqlite3)

# 创建 SQLite3 库目标
add_library(sqlite3_lib STATIC ${sqlite3_SOURCE_DIR}/sqlite3.c)
target_include_directories(sqlite3_lib PUBLIC ${sqlite3_SOURCE_DIR})

# 创建别名以兼容原有代码
add_library(SQLite::SQLite3 ALIAS sqlite3_lib)
set(SQLite3_FOUND TRUE)

# ==========================================
# 3. 头文件路径
# ==========================================
# 将根目录下的 include 文件夹加入编译搜索路径
# 这样在代码中就可以直接写 #include "DBManager.h" 而不用加路径
include_directories(${CMAKE_SOURCE_DIR}/include)

# ==========================================
# 4. 源文件定义
# ==========================================
# 根据你的 tree 结构，显式指定源文件位置
set(SOURCE_FILES
    # 核心业务逻辑
    src/core/main.cpp
    src/data/MetroToolkit.cpp
    
    # 数据层
    src/data/DBManager.cpp
    
    # 如果未来有 bindings (如 Python 接口)，加在这里
    # src/bindings/python_bindings.cpp 
)

# ==========================================
# 5. 生成可执行文件
# ==========================================
add_executable(${PROJECT_NAME} ${SOURCE_FILES})

# ==========================================
# 6. 链接库
# ==========================================
target_link_libraries(${PROJECT_NAME} PRIVATE SQLite::SQLite3)
message(STATUS "SQLite3 configured and will be linked.")

# ==========================================
# 7. 调试信息 (可选)
# ==========================================
message(STATUS "Project Source Dir: ${CMAKE_SOURCE_DIR}")
message(STATUS "Source Files: ${SOURCE_FILES}")
