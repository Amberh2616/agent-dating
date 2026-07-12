"""
A* 尋路系統
A* Pathfinding System - Habbo-style 8-direction movement
"""

import heapq
from typing import List, Tuple, Optional, Set, Dict
from dataclasses import dataclass, field


@dataclass(order=True)
class Node:
    """尋路節點"""
    f_score: float
    position: Tuple[int, int] = field(compare=False)
    g_score: float = field(default=0, compare=False)
    parent: Optional['Node'] = field(default=None, compare=False)


# 8 方向移動 (Habbo 風格)
# 方向對應: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW
DIRECTIONS = [
    (0, -1),   # 0: North
    (1, -1),   # 1: Northeast (diagonal)
    (1, 0),    # 2: East
    (1, 1),    # 3: Southeast (diagonal)
    (0, 1),    # 4: South
    (-1, 1),   # 5: Southwest (diagonal)
    (-1, 0),   # 6: West
    (-1, -1),  # 7: Northwest (diagonal)
]

# 斜向移動成本 (約 1.414)
DIAGONAL_COST = 1.414
STRAIGHT_COST = 1.0


def get_direction(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> int:
    """
    根據兩點計算面向方向 (0-7)
    """
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]

    # 正規化
    if dx != 0:
        dx = dx // abs(dx)
    if dy != 0:
        dy = dy // abs(dy)

    # 查找對應方向
    for i, (ddx, ddy) in enumerate(DIRECTIONS):
        if dx == ddx and dy == ddy:
            return i

    return 2  # 預設面向東


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """
    啟發函數 - 使用 Chebyshev 距離 (8方向移動)
    """
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return max(dx, dy) + (DIAGONAL_COST - 1) * min(dx, dy)


def get_neighbors(
    pos: Tuple[int, int],
    width: int,
    height: int,
    obstacles: Set[Tuple[int, int]],
    agent_positions: Set[Tuple[int, int]] = None
) -> List[Tuple[Tuple[int, int], float]]:
    """
    取得可移動的鄰居節點和移動成本

    Args:
        pos: 當前位置
        width: 房間寬度
        height: 房間高度
        obstacles: 障礙物集合 (家具等)
        agent_positions: 其他 Agent 位置集合

    Returns:
        List of (position, cost) tuples
    """
    if agent_positions is None:
        agent_positions = set()

    neighbors = []
    x, y = pos

    for i, (dx, dy) in enumerate(DIRECTIONS):
        nx, ny = x + dx, y + dy

        # 邊界檢查
        if not (0 <= nx < width and 0 <= ny < height):
            continue

        # 障礙物檢查
        if (nx, ny) in obstacles:
            continue

        # 其他 Agent 檢查 (避免碰撞)
        if (nx, ny) in agent_positions:
            continue

        # 斜向移動需要檢查相鄰格子
        if dx != 0 and dy != 0:
            # 斜向移動時，兩側必須都可通行
            if (x + dx, y) in obstacles or (x, y + dy) in obstacles:
                continue
            if (x + dx, y) in agent_positions or (x, y + dy) in agent_positions:
                continue
            cost = DIAGONAL_COST
        else:
            cost = STRAIGHT_COST

        neighbors.append(((nx, ny), cost))

    return neighbors


def find_path(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    width: int,
    height: int,
    obstacles: Set[Tuple[int, int]] = None,
    agent_positions: Set[Tuple[int, int]] = None,
    max_iterations: int = 1000
) -> Optional[List[Tuple[int, int]]]:
    """
    A* 尋路演算法

    Args:
        start: 起點 (x, y)
        goal: 終點 (x, y)
        width: 房間寬度
        height: 房間高度
        obstacles: 障礙物集合
        agent_positions: 其他 Agent 位置 (不包含自己)
        max_iterations: 最大迭代次數

    Returns:
        路徑列表 [(x1, y1), (x2, y2), ...] 或 None (無法到達)
    """
    if obstacles is None:
        obstacles = set()
    if agent_positions is None:
        agent_positions = set()

    # 起點或終點是障礙物
    if start in obstacles or goal in obstacles:
        return None

    # 如果終點被 Agent 佔據，嘗試找附近的點
    if goal in agent_positions:
        goal = find_nearest_free_position(goal, width, height, obstacles, agent_positions)
        if goal is None:
            return None

    # 起點就是終點
    if start == goal:
        return [start]

    # A* 演算法
    open_set = []
    start_node = Node(
        f_score=heuristic(start, goal),
        position=start,
        g_score=0
    )
    heapq.heappush(open_set, start_node)

    # 記錄最佳路徑
    came_from: Dict[Tuple[int, int], Node] = {}
    g_scores: Dict[Tuple[int, int], float] = {start: 0}

    iterations = 0

    while open_set and iterations < max_iterations:
        iterations += 1
        current = heapq.heappop(open_set)

        # 到達目標
        if current.position == goal:
            return reconstruct_path(current)

        # 遍歷鄰居
        for neighbor_pos, cost in get_neighbors(
            current.position, width, height, obstacles, agent_positions
        ):
            tentative_g = current.g_score + cost

            if neighbor_pos not in g_scores or tentative_g < g_scores[neighbor_pos]:
                g_scores[neighbor_pos] = tentative_g
                f_score = tentative_g + heuristic(neighbor_pos, goal)

                neighbor_node = Node(
                    f_score=f_score,
                    position=neighbor_pos,
                    g_score=tentative_g,
                    parent=current
                )

                heapq.heappush(open_set, neighbor_node)

    # 找不到路徑
    return None


def reconstruct_path(node: Node) -> List[Tuple[int, int]]:
    """
    從目標節點回溯建構路徑
    """
    path = []
    current = node

    while current is not None:
        path.append(current.position)
        current = current.parent

    path.reverse()
    return path


def find_nearest_free_position(
    target: Tuple[int, int],
    width: int,
    height: int,
    obstacles: Set[Tuple[int, int]],
    agent_positions: Set[Tuple[int, int]],
    max_distance: int = 3
) -> Optional[Tuple[int, int]]:
    """
    找到最近的空閒位置 (用於接近被佔據的目標)

    Args:
        target: 目標位置
        width: 房間寬度
        height: 房間高度
        obstacles: 障礙物集合
        agent_positions: Agent 位置集合
        max_distance: 最大搜索距離

    Returns:
        最近的空閒位置或 None
    """
    x, y = target

    for distance in range(1, max_distance + 1):
        # 按距離搜索
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if abs(dx) != distance and abs(dy) != distance:
                    continue  # 只檢查當前距離的格子

                nx, ny = x + dx, y + dy

                # 邊界檢查
                if not (0 <= nx < width and 0 <= ny < height):
                    continue

                # 檢查是否空閒
                if (nx, ny) not in obstacles and (nx, ny) not in agent_positions:
                    return (nx, ny)

    return None


def smooth_path(path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    路徑平滑 - 移除不必要的中間點

    使用直線可達性檢測來減少路徑點
    """
    if len(path) <= 2:
        return path

    smoothed = [path[0]]
    current_idx = 0

    while current_idx < len(path) - 1:
        # 嘗試跳過中間點
        best_idx = current_idx + 1

        for check_idx in range(current_idx + 2, len(path)):
            # 檢查是否可以直線到達
            if is_line_walkable(path[current_idx], path[check_idx], path):
                best_idx = check_idx

        smoothed.append(path[best_idx])
        current_idx = best_idx

    return smoothed


def is_line_walkable(
    start: Tuple[int, int],
    end: Tuple[int, int],
    path: List[Tuple[int, int]]
) -> bool:
    """
    檢查兩點之間是否可以直線移動
    (簡化版：只檢查路徑中的點是否在直線上)
    """
    sx, sy = start
    ex, ey = end

    dx = ex - sx
    dy = ey - sy
    steps = max(abs(dx), abs(dy))

    if steps == 0:
        return True

    # 簡單的直線可達性：檢查路徑是否包含這些點
    path_set = set(path)

    for i in range(1, steps):
        x = sx + dx * i // steps
        y = sy + dy * i // steps
        if (x, y) not in path_set:
            # 中間點不在原路徑中，可能有障礙
            return False

    return True


def calculate_path_with_directions(
    path: List[Tuple[int, int]]
) -> List[Dict]:
    """
    計算帶方向的路徑點 (供前端使用)

    Returns:
        [{"x": 0, "y": 0, "direction": 2}, ...]
    """
    if not path:
        return []

    result = []

    for i, pos in enumerate(path):
        if i < len(path) - 1:
            direction = get_direction(pos, path[i + 1])
        elif i > 0:
            direction = get_direction(path[i - 1], pos)
        else:
            direction = 2  # 預設面向東

        result.append({
            "x": pos[0],
            "y": pos[1],
            "direction": direction
        })

    return result


def get_walkable_tiles_from_room(room) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    """
    從房間模型提取可行走區域和障礙物

    Args:
        room: Room model instance

    Returns:
        (walkable_tiles, obstacles)
    """
    obstacles = set()

    # 從 floor_plan 解析 (0 = 可走, 1 = 障礙)
    if room.floor_plan:
        for y, row in enumerate(room.floor_plan):
            for x, tile in enumerate(row):
                if tile == 1:
                    obstacles.add((x, y))

    # 從 furniture 解析障礙物
    if room.furniture:
        for item in room.furniture:
            x = item.get('x', 0)
            y = item.get('y', 0)
            w = item.get('width', 1)
            h = item.get('height', 1)

            for dx in range(w):
                for dy in range(h):
                    obstacles.add((x + dx, y + dy))

    return obstacles


def get_agent_positions_in_room(room, exclude_agent_id=None) -> Set[Tuple[int, int]]:
    """
    取得房間內所有 Agent 的位置

    Args:
        room: Room model instance
        exclude_agent_id: 要排除的 Agent ID (通常是自己)

    Returns:
        Set of (x, y) positions
    """
    from apps.world.models import AgentPosition

    positions = set()

    agent_positions = AgentPosition.objects.filter(room=room)
    if exclude_agent_id:
        agent_positions = agent_positions.exclude(agent_id=exclude_agent_id)

    for pos in agent_positions:
        positions.add((pos.x, pos.y))

    return positions


def find_path_in_room(
    room,
    start: Tuple[int, int],
    goal: Tuple[int, int],
    exclude_agent_id=None
) -> Optional[List[Dict]]:
    """
    在房間中尋路的高層 API

    Args:
        room: Room model instance
        start: 起點 (x, y)
        goal: 終點 (x, y)
        exclude_agent_id: 要排除的 Agent ID

    Returns:
        帶方向的路徑列表 [{"x": 0, "y": 0, "direction": 2}, ...] 或 None
    """
    obstacles = get_walkable_tiles_from_room(room)
    agent_positions = get_agent_positions_in_room(room, exclude_agent_id)

    path = find_path(
        start=start,
        goal=goal,
        width=room.width,
        height=room.height,
        obstacles=obstacles,
        agent_positions=agent_positions
    )

    if path is None:
        return None

    # 平滑路徑
    smoothed = smooth_path(path)

    # 轉換為帶方向的格式
    return calculate_path_with_directions(smoothed)


# 測試函數
def test_pathfinding():
    """
    簡單測試
    """
    # 10x10 房間，中間有障礙物
    width, height = 10, 10
    obstacles = {(4, 3), (4, 4), (4, 5), (4, 6)}  # 一堵牆

    start = (2, 5)
    goal = (7, 5)

    path = find_path(start, goal, width, height, obstacles)

    if path:
        print(f"Path found: {path}")
        print(f"Path with directions: {calculate_path_with_directions(path)}")
    else:
        print("No path found")


if __name__ == "__main__":
    test_pathfinding()
