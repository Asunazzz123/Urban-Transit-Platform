cmake_minimum_required(VERSION 3.14)

# 使用你的文件夹名称作为项目名
project(transit-routing-engine VERSION 1.0)

# ==========================================
# 1. C++ 标准 (C++17)
# ==========================================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ==========================================
# 2. 依赖查找 (SQLite3)
# ==========================================
find_package(SQLite3 REQUIRED)

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
    src/core/MetroToolkit.cpp
    
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
if(SQLite3_FOUND)
    target_link_libraries(${PROJECT_NAME} PRIVATE SQLite::SQLite3)
    message(STATUS "SQLite3 found and linked.")
endif()

# ==========================================
# 7. 调试信息 (可选)
# ==========================================
message(STATUS "Project Source Dir: ${CMAKE_SOURCE_DIR}")
message(STATUS "Source Files: ${SOURCE_FILES}")