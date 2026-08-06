from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import math
from collections import deque
import copy

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Configuration ---
PLAN_COUNT = 3
ROOM_PADDING = 1.0
CORRIDOR_WIDTH = 4.0
CORRIDOR_DISTANCE_THRESHOLD = 10000.0
MAIN_ENTRANCE_WIDTH = 6.0
MAIN_ENTRANCE_LENGTH = 4.0
INITIAL_OFFSET = 20.0

# Door and Wall Constants
DOOR_WIDTH = 3.0
WALL_TOLERANCE = 1.0
GAP_MIN_DISTANCE_FT = 0.5
MIN_CONNECT_GAP_FT = 3.0

# Room Properties and Adjacency Preferences
room_properties = {
    "Master Bedroom": {"doors": ["S", "E", "W"], "windows": ["N", "E"], "color": "#A93226"},
    "Bedroom": {"doors": ["S", "E", "W"], "windows": ["N", "E"], "color": "#1F618D"},
    "Office": {"doors": ["S"], "windows": ["N"], "color": "#1D8348"},
    "Workshop": {"doors": ["S", "W"], "windows": ["N"], "color": "#9A7D0A"},
    "Gym": {"doors": ["S"], "windows": ["N", "E"], "color": "#884EA0"},
    "Pet Room": {"doors": ["S"], "windows": ["N", "E", "W"], "color": "#5D6D7E"},
    "Kids Room": {"doors": ["S", "E"], "windows": ["N", "W"], "color": "#D35400"},
    "Guest Room": {"doors": ["S"], "windows": ["N"], "color": "#626567"},
    "Living Room": {"doors": ["N", "S", "E", "W"], "windows": ["N", "S", "E", "W"], "color": "#27AE60"},
    "Family Room": {"doors": ["N", "S"], "windows": ["E", "W"], "color": "#3498DB"},
    "Dining Room": {"doors": ["N", "S", "E", "W"], "windows": ["S", "W"], "color": "#F39C12"},
    "Kitchen": {"doors": ["N", "W"], "windows": ["E"], "color": "#D68910"},
    "Bathroom": {"doors": ["N", "E"], "windows": ["W"], "color": "#7D3C98"},
    "Guest Bathroom": {"doors": ["N", "E"], "windows": ["W"], "color": "#A569BD"},
    "Elderly Bathroom": {"doors": ["N", "E"], "windows": ["W"], "color": "#6C3483"},
    "Utility Room": {"doors": ["N", "S"], "windows": ["W"], "color": "#4A235A"},
    "Storage Room": {"doors": ["N", "S"], "windows": [None], "color": "#34495E"},
    "Corridor": {"doors": [None], "windows": [None],"color": "rgba(180, 190, 200, 0.3)"},
    "Plan Size": {"doors": [None], "windows": [None], "color": "#FADBD8"},
    "Terrace/Balcony": {"doors": ["N", "S", "E", "W"], "windows": [None], "color": "#82E0AA"},
    "Main Entrance": {"doors": ["N"], "windows": [None], "color": "#FF5733"},
}

adjacency_preferences = {
    "Living Room": ["Dining Room", "Kitchen", "Corridor", "Main Entrance"],
    "Family Room": ["Living Room", "Kids Room", "Corridor", "Main Entrance"],
    "Dining Room": ["Living Room", "Kitchen", "Corridor"],
    "Kitchen": ["Dining Room", "Living Room", "Utility Room", "Corridor"],
    "Master Bedroom": ["Bathroom", "Corridor"],
    "Bedroom": ["Bathroom", "Corridor"],
    "Office": ["Living Room", "Corridor"],
    "Utility Room": ["Kitchen", "Storage Room"],
    "Gym": ["Utility Room"],
}


def is_real_room(room):
    if room.get('is_corridor', False):
        return False
    if room.get('is_entrance', False):
        return False
    if room.get('room') in ["Plan Size", "Corridor", "Main Entrance"]:
        return False
    return True


def get_adjacency_map(rooms):
    adj = {room['id']: [] for room in rooms if 'id' in room}
    room_list = [
        r for r in rooms
        if 'x' in r and r['x'] is not None
        and r['room'] not in ["Plan Size"]
    ]
    for i in range(len(room_list)):
        for j in range(i + 1, len(room_list)):
            room1 = room_list[i]
            room2 = room_list[j]
            if find_shared_wall(room1, room2):
                if room1['id'] not in adj:
                    adj[room1['id']] = []
                if room2['id'] not in adj:
                    adj[room2['id']] = []
                adj[room1['id']].append(room2['id'])
                adj[room2['id']].append(room1['id'])
    return adj


def check_connectivity(rooms, adjacency_map):
    key_rooms = [
        r for r in rooms
        if r['room'] not in ["Plan Size", "Corridor", "Storage Room"]
    ]
    start_nodes = [
        r['id'] for r in key_rooms
        if r['room'] in ["Main Entrance", "Living Room", "Family Room"]
    ]
    if not start_nodes:
        return {
            "is_connected": False,
            "unreachable_rooms": [{"name": r['room'], "id": r['id']} for r in key_rooms],
        }
    visited = set()
    queue = deque(start_nodes)
    while queue:
        current_id = queue.popleft()
        if current_id not in visited:
            visited.add(current_id)
            for neighbor_id in adjacency_map.get(current_id, []):
                if neighbor_id not in visited:
                    queue.append(neighbor_id)
    unreachable_rooms = [
        {"name": r['room'], "id": r['id']}
        for r in key_rooms if r['id'] not in visited
    ]
    return {"is_connected": len(unreachable_rooms) == 0, "unreachable_rooms": unreachable_rooms}


def check_design_rules(rooms, adjacency_map):
    rooms_by_id = {r['id']: r for r in rooms if 'id' in r}
    warnings = []
    bedroom_types = ["Master Bedroom", "Bedroom", "Guest Room", "Kids Room"]
    bathroom_types = ["Bathroom", "Guest Bathroom", "Elderly Bathroom"]
    for room_id, neighbors_id in adjacency_map.items():
        room = rooms_by_id.get(room_id)
        if not room:
            continue
        if room['room'] in bathroom_types:
            non_bedroom_access = any(
                rooms_by_id.get(n, {}).get('room') not in bedroom_types
                and rooms_by_id.get(n, {}).get('room') != 'Corridor'
                for n in neighbors_id
            )
            if not non_bedroom_access and neighbors_id:
                warnings.append({
                    "type": "Access Isolation",
                    "room": room['room'],
                    "description": f"Warning: {room['room']} is only accessible from bedrooms.",
                })
        if room['room'] in ["Living Room", "Family Room"]:
            has_entrance = any(
                rooms_by_id.get(n, {}).get('room') in ["Main Entrance", "Corridor"]
                for n in neighbors_id
            )
            if not has_entrance:
                warnings.append({
                    "type": "Core Access Issue",
                    "room": room['room'],
                    "description": f"Warning: {room['room']} not connected to Main Entrance or Corridor.",
                })
    return warnings


def calculate_room_gaps(rooms):
    gaps = []
    room_list = [r for r in rooms if 'x' in r and r['x'] is not None and is_real_room(r)]
    for i in range(len(room_list)):
        for j in range(i + 1, len(room_list)):
            room1 = room_list[i]
            room2 = room_list[j]
            if find_shared_wall(room1, room2):
                continue
            r1_x1, r1_y1 = room1['x'], room1['y']
            r1_x2, r1_y2 = r1_x1 + room1['width'], r1_y1 + room1['length']
            r2_x1, r2_y1 = room2['x'], room2['y']
            r2_x2, r2_y2 = r2_x1 + room2['width'], r2_y1 + room2['length']
            dx = 0
            if r1_x2 < r2_x1:
                dx = r2_x1 - r1_x2
            elif r2_x2 < r1_x1:
                dx = r1_x1 - r2_x2
            dy = 0
            if r1_y2 < r2_y1:
                dy = r2_y1 - r1_y2
            elif r2_y2 < r1_y1:
                dy = r1_y1 - r2_y2
            horizontal_overlap = max(r1_x1, r2_x1) < min(r1_x2, r2_x2)
            vertical_overlap = max(r1_y1, r2_y1) < min(r1_y2, r2_y2)
            if vertical_overlap and dx > GAP_MIN_DISTANCE_FT:
                overlap_y = max(r1_y1, r2_y1) + (min(r1_y2, r2_y2) - max(r1_y1, r2_y1)) / 2
                start_x = r1_x2 if r1_x2 < r2_x1 else r2_x2
                gaps.append({
                    "room1": room1['room'], "room2": room2['room'],
                    "distance_ft": round(dx, 1), "type": "H",
                    "x1": round(start_x, 2), "y1": round(overlap_y, 2),
                    "x2": round(start_x + dx, 2), "y2": round(overlap_y, 2),
                })
            elif horizontal_overlap and dy > GAP_MIN_DISTANCE_FT:
                overlap_x = max(r1_x1, r2_x1) + (min(r1_x2, r2_x2) - max(r1_x1, r2_x1)) / 2
                start_y = r1_y2 if r1_y2 < r2_y1 else r2_y2
                gaps.append({
                    "room1": room1['room'], "room2": room2['room'],
                    "distance_ft": round(dy, 1), "type": "V",
                    "x1": round(overlap_x, 2), "y1": round(start_y, 2),
                    "x2": round(overlap_x, 2), "y2": round(start_y + dy, 2),
                })
    return gaps


def find_min_gap_distance(room1, room2):
    r1_x1, r1_y1 = room1['x'], room1['y']
    r1_x2, r1_y2 = r1_x1 + room1['width'], r1_y1 + room1['length']
    r2_x1, r2_y1 = room2['x'], room2['y']
    r2_x2, r2_y2 = r2_x1 + room2['width'], r2_y1 + room2['length']
    dx = max(r1_x1 - r2_x2, r2_x1 - r1_x2, 0)
    dy = max(r1_y1 - r2_y2, r2_y1 - r1_y2, 0)
    horizontal_overlap = max(r1_x1, r2_x1) < min(r1_x2, r2_x2)
    vertical_overlap = max(r1_y1, r2_y1) < min(r1_y2, r2_y2)
    if vertical_overlap and dx > 0:
        return dx, 'H'
    elif horizontal_overlap and dy > 0:
        return dy, 'V'
    return math.sqrt(dx ** 2 + dy ** 2), 'D'


def is_overlapping(new_room, placed_rooms, padding=ROOM_PADDING):
    nx1 = new_room['x'] - padding
    ny1 = new_room['y'] - padding
    nx2 = new_room['x'] + new_room['width'] + padding
    ny2 = new_room['y'] + new_room['length'] + padding
    for r in placed_rooms:
        if 'id' in r and 'id' in new_room and r['id'] == new_room['id']:
            continue
        rx1, ry1 = r['x'], r['y']
        rx2, ry2 = rx1 + r['width'], ry1 + r['length']
        if nx1 < rx2 and nx2 > rx1 and ny1 < ry2 and ny2 > ry1:
            return True
    return False


def find_shared_wall(room1, room2):
    r1_x1, r1_y1 = room1['x'], room1['y']
    r1_x2, r1_y2 = r1_x1 + room1['width'], r1_y1 + room1['length']
    r2_x1, r2_y1 = room2['x'], room2['y']
    r2_x2, r2_y2 = r2_x1 + room2['width'], r2_y1 + room2['length']

    if abs(r1_x2 - r2_x1) < WALL_TOLERANCE or abs(r2_x2 - r1_x1) < WALL_TOLERANCE:
        overlap_y1 = max(r1_y1, r2_y1)
        overlap_y2 = min(r1_y2, r2_y2)
        if overlap_y2 - overlap_y1 > DOOR_WIDTH:
            shared_x = r1_x2 if abs(r1_x2 - r2_x1) < WALL_TOLERANCE else r2_x2
            return {"direction": "V", "x": shared_x, "y": overlap_y1 + (overlap_y2 - overlap_y1) / 2, "length": DOOR_WIDTH}

    if abs(r1_y2 - r2_y1) < WALL_TOLERANCE or abs(r2_y2 - r1_y1) < WALL_TOLERANCE:
        overlap_x1 = max(r1_x1, r2_x1)
        overlap_x2 = min(r1_x2, r2_x2)
        if overlap_x2 - overlap_x1 > DOOR_WIDTH:
            shared_y = r1_y2 if abs(r1_y2 - r2_y1) < WALL_TOLERANCE else r2_y2
            return {"direction": "H", "x": overlap_x1 + (overlap_x2 - overlap_x1) / 2, "y": shared_y, "length": DOOR_WIDTH}

    return None

def has_corridor_between(room1, room2, corridors):
    for c in corridors:
        connecting = c.get("connecting", [])
        if room1['room'] in connecting and room2['room'] in connecting:
            return True
    return False


def add_inter_room_doors(final_rooms):
    doors = []

    rooms_with_coords = [
        r for r in final_rooms
        if 'x' in r and r['x'] is not None and r['room'] not in ["Plan Size"]
    ]

    added_pairs = set()

    corridors = [r for r in rooms_with_coords if r.get('is_corridor', False)]
    normal_rooms = [r for r in rooms_with_coords if not r.get('is_corridor', False)]

    # 1. Doors between normal rooms only
    for i in range(len(normal_rooms)):
        for j in range(i + 1, len(normal_rooms)):
            room1 = normal_rooms[i]
            room2 = normal_rooms[j]

            # Skip if corridor connects them
            if has_corridor_between(room1, room2, corridors):
                continue

            pair_key = tuple(sorted([room1['id'], room2['id']]))
            if pair_key in added_pairs:
                continue

            wall_details = find_shared_wall(room1, room2)

            if wall_details:
                added_pairs.add(pair_key)

                doors.append({
                    "type": "Door",
                    "direction": wall_details['direction'],
                    "x": round(wall_details['x'], 2),
                    "y": round(wall_details['y'], 2),
                    "length": wall_details['length'],
                    "rooms_connected": [room1['room'], room2['room']],
                    "is_corridor_door": False,
                })

    # 2. Corridor doors (ONLY endpoints)
    for corridor in corridors:
        adjacent_rooms = []

        for room in rooms_with_coords:
            if room['id'] == corridor['id']:
                continue

            wall_details = find_shared_wall(corridor, room)
            if wall_details:
                adjacent_rooms.append((room, wall_details))

        if not adjacent_rooms:
            continue

        # Sort based on orientation
        is_horizontal = corridor['width'] >= corridor['length']

        if is_horizontal:
            adjacent_rooms.sort(key=lambda x: x[0]['x'])
        else:
            adjacent_rooms.sort(key=lambda x: x[0]['y'])

        # Pick endpoints only
        if len(adjacent_rooms) == 1:
            endpoints = [adjacent_rooms[0]]
        else:
            endpoints = [adjacent_rooms[0], adjacent_rooms[-1]]

        for room, wall_details in endpoints:
            pair_key = tuple(sorted([corridor['id'], room['id']]))

            if pair_key in added_pairs:
                continue

            added_pairs.add(pair_key)

            doors.append({
                "type": "Door",
                "direction": wall_details['direction'],
                "x": round(wall_details['x'], 2),
                "y": round(wall_details['y'], 2),
                "length": wall_details['length'],
                "rooms_connected": [corridor['room'], room['room']],
                "is_corridor_door": True,
            })

    return doors

def add_corridors_for_unreachable(placed_rooms, final_rooms_ref, corridor_id_start=8000):
    """
    Post-placement pass: for any unreachable room, insert a corridor to the
    nearest connected room so the plan is fully connected.
    """
    corridor_id = corridor_id_start
    corridor_color = room_properties["Corridor"]["color"]

    for _ in range(10):  # max 10 passes
        adj_map = get_adjacency_map(placed_rooms)
        connectivity = check_connectivity(placed_rooms, adj_map)
        if connectivity['is_connected']:
            break
        unreachable = connectivity['unreachable_rooms']
        if not unreachable:
            break

        unreachable_ids = {u['id'] for u in unreachable}
        connected_rooms = [
            r for r in placed_rooms
            if r['room'] not in ["Plan Size"] and r['id'] not in unreachable_ids
            and 'x' in r and r['x'] is not None
        ]

        if not connected_rooms:
            break

        made_connection = False
        for u_info in unreachable:
            target = next((r for r in placed_rooms if r['id'] == u_info['id']), None)
            if not target:
                continue

            # Find closest connected room with H or V gap
            best_cr = None
            best_gap = float('inf')
            best_dir = None
            for cr in connected_rooms:
                gap, direction = find_min_gap_distance(target, cr)
                if direction in ['H', 'V'] and gap < best_gap:
                    best_gap = gap
                    best_cr = cr
                    best_dir = direction

            if not best_cr or best_gap < MIN_CONNECT_GAP_FT:
                continue

            r1_x1, r1_y1 = target['x'], target['y']
            r1_x2, r1_y2 = r1_x1 + target['width'], r1_y1 + target['length']
            r2_x1, r2_y1 = best_cr['x'], best_cr['y']
            r2_x2, r2_y2 = r2_x1 + best_cr['width'], r2_y1 + best_cr['length']

            new_corridor = None

            if best_dir == 'H':
                overlap_y1 = max(r1_y1, r2_y1)
                overlap_y2 = min(r1_y2, r2_y2)
                overlap = overlap_y2 - overlap_y1
                if overlap >= DOOR_WIDTH:
                    corr_x = r1_x2 if r1_x2 < r2_x1 else r2_x2
                    corr_w = abs(r2_x1 - r1_x2) if r1_x2 < r2_x1 else abs(r1_x1 - r2_x2)
                    c_y = overlap_y1 + overlap / 2
                    corr_l = min(CORRIDOR_WIDTH, overlap)
                    corr_y = c_y - corr_l / 2
                    new_corridor = {
                        "id": corridor_id, "room": "Corridor", "name": "Corridor",
                        "x": round(corr_x, 2), "y": round(corr_y, 2),
                        "width": round(corr_w, 2), "length": round(corr_l, 2),
                        "area_sqft": round(corr_w * corr_l, 2),
                        "color": corridor_color, "is_corridor": True,
                        "door_direction": None, "window_direction": None, "is_entrance": False,
                        "connecting": [target['room'], best_cr['room']],
                    }

            elif best_dir == 'V':
                overlap_x1 = max(r1_x1, r2_x1)
                overlap_x2 = min(r1_x2, r2_x2)
                overlap = overlap_x2 - overlap_x1
                if overlap >= DOOR_WIDTH:
                    corr_y = r1_y2 if r1_y2 < r2_y1 else r2_y2
                    corr_l = abs(r2_y1 - r1_y2) if r1_y2 < r2_y1 else abs(r1_y1 - r2_y2)
                    c_x = overlap_x1 + overlap / 2
                    corr_w = min(CORRIDOR_WIDTH, overlap)
                    corr_x = c_x - corr_w / 2
                    new_corridor = {
                        "id": corridor_id, "room": "Corridor", "name": "Corridor",
                        "x": round(corr_x, 2), "y": round(corr_y, 2),
                        "width": round(corr_w, 2), "length": round(corr_l, 2),
                        "area_sqft": round(corr_w * corr_l, 2),
                        "color": corridor_color, "is_corridor": True,
                        "door_direction": None, "window_direction": None, "is_entrance": False,
                        "connecting": [target['room'], best_cr['room']],
                    }

            if new_corridor:
                placed_rooms.append(new_corridor)
                final_rooms_ref.append(new_corridor)
                corridor_id += 1
                made_connection = True

        if not made_connection:
            break

    return placed_rooms


def force_kitchen_near_living_room(placed_rooms):
    """Force Kitchen to be directly adjacent to Living Room."""
    living_room = next((r for r in placed_rooms if r['room'] == 'Living Room'), None)
    kitchen = next((r for r in placed_rooms if r['room'] == 'Kitchen'), None)
    if not living_room or not kitchen:
        return placed_rooms
    if find_shared_wall(living_room, kitchen):
        return placed_rooms

    other_rooms = [r for r in placed_rooms if r['id'] != kitchen['id']]
    sides = [
        ('E', living_room['x'] + living_room['width'], living_room['y'] + (living_room['length'] - kitchen['length']) / 2),
        ('W', living_room['x'] - kitchen['width'],     living_room['y'] + (living_room['length'] - kitchen['length']) / 2),
        ('S', living_room['x'] + (living_room['width'] - kitchen['width']) / 2, living_room['y'] + living_room['length']),
        ('N', living_room['x'] + (living_room['width'] - kitchen['width']) / 2, living_room['y'] - kitchen['length']),
    ]
    for side, new_x, new_y in sides:
        new_x = max(0.0, new_x)
        new_y = max(0.0, new_y)
        temp = copy.deepcopy(kitchen)
        temp['x'] = new_x
        temp['y'] = new_y
        if not is_overlapping(temp, other_rooms, padding=0.0):
            kitchen['x'] = new_x
            kitchen['y'] = new_y
            return placed_rooms

    # Try with small offsets
    for side, new_x, new_y in sides:
        for off in [2.0, -2.0, 4.0, -4.0]:
            nx = max(0.0, new_x + (off if side in ['E', 'W'] else 0))
            ny = max(0.0, new_y + (off if side in ['N', 'S'] else 0))
            temp = copy.deepcopy(kitchen)
            temp['x'] = nx
            temp['y'] = ny
            if not is_overlapping(temp, other_rooms, padding=0.0):
                kitchen['x'] = nx
                kitchen['y'] = ny
                return placed_rooms
    return placed_rooms


def fit_and_connect_rooms(rooms, main_room_id, max_fit_distance=1.5, min_connect_gap=MIN_CONNECT_GAP_FT):
    placed_rooms = [r for r in rooms if 'x' in r and r['x'] is not None and r['room'] != "Plan Size"]
    rooms_by_id = {r['id']: r for r in placed_rooms}
    main_room = rooms_by_id.get(main_room_id)
    if not main_room:
        return rooms

    rooms_to_modify = copy.deepcopy(placed_rooms)
    made_change = True
    while made_change:
        made_change = False
        for i in range(len(rooms_to_modify)):
            if rooms_to_modify[i]['id'] == main_room_id:
                continue
            for j in range(len(rooms_to_modify)):
                if i == j:
                    continue
                room1 = rooms_to_modify[i]
                room2 = rooms_to_modify[j]
                if find_shared_wall(room1, room2):
                    continue
                gap, direction = find_min_gap_distance(room1, room2)
                if direction in ['H', 'V'] and WALL_TOLERANCE < gap <= max_fit_distance:
                    temp_room = copy.deepcopy(room1)
                    if direction == 'H':
                        if room1['x'] + room1['width'] < room2['x']:
                            temp_room['x'] += room2['x'] - (room1['x'] + room1['width']) - WALL_TOLERANCE
                        else:
                            temp_room['x'] -= room1['x'] - (room2['x'] + room2['width']) - WALL_TOLERANCE
                    elif direction == 'V':
                        if room1['y'] + room1['length'] < room2['y']:
                            temp_room['y'] += room2['y'] - (room1['y'] + room1['length']) - WALL_TOLERANCE
                        else:
                            temp_room['y'] -= room1['y'] - (room2['y'] + room2['length']) - WALL_TOLERANCE
                    if not is_overlapping(temp_room, [r for r in rooms_to_modify if r['id'] != room1['id']], padding=ROOM_PADDING):
                        rooms_to_modify[i]['x'] = temp_room['x']
                        rooms_to_modify[i]['y'] = temp_room['y']
                        made_change = True
                        break
            if made_change:
                break

    for room in rooms_to_modify:
        orig = rooms_by_id.get(room['id'])
        if orig:
            orig['x'] = room['x']
            orig['y'] = room['y']
    return placed_rooms


def snap_preferred_adjacent_rooms(placed_rooms):
    modified = True
    max_iterations = 10
    iteration = 0
    while modified and iteration < max_iterations:
        modified = False
        iteration += 1
        for room in placed_rooms:
            if room['room'] not in adjacency_preferences:
                continue
            for pref in adjacency_preferences[room['room']]:
                for other in placed_rooms:
                    if other['id'] == room['id'] or other['room'] != pref:
                        continue
                    gap, direction = find_min_gap_distance(room, other)
                    if direction in ['H', 'V'] and 0 < gap <= ROOM_PADDING + 0.5:
                        tr = copy.deepcopy(room)
                        to = copy.deepcopy(other)
                        if direction == 'H':
                            if room['x'] + room['width'] < other['x']:
                                to['x'] = room['x'] + room['width']
                            else:
                                tr['x'] = other['x'] + other['width']
                        elif direction == 'V':
                            if room['y'] + room['length'] < other['y']:
                                to['y'] = room['y'] + room['length']
                            else:
                                tr['y'] = other['y'] + other['length']
                        if (not is_overlapping(tr, [r for r in placed_rooms if r['id'] != room['id']], padding=0.0)
                                and not is_overlapping(to, [r for r in placed_rooms if r['id'] != other['id']], padding=0.0)):
                            room['x'], room['y'] = tr['x'], tr['y']
                            other['x'], other['y'] = to['x'], to['y']
                            modified = True
                            break
                if modified:
                    break
            if modified:
                break
    return placed_rooms


def snap_living_room_adjacent(placed_rooms):
    modified = True
    max_iterations = 10
    iteration = 0
    while modified and iteration < max_iterations:
        modified = False
        iteration += 1
        for room in placed_rooms:
            if room['room'] != "Living Room":
                continue
            for other in placed_rooms:
                if other['id'] == room['id'] or other['room'] == "Plan Size":
                    continue
                gap, direction = find_min_gap_distance(room, other)
                if direction in ['H', 'V'] and 0 < gap <= ROOM_PADDING:
                    tr = copy.deepcopy(room)
                    to = copy.deepcopy(other)
                    if direction == 'H':
                        if room['x'] + room['width'] < other['x']:
                            to['x'] = room['x'] + room['width']
                        else:
                            tr['x'] = other['x'] + other['width']
                    elif direction == 'V':
                        if room['y'] + room['length'] < other['y']:
                            to['y'] = room['y'] + room['length']
                        else:
                            tr['y'] = other['y'] + other['length']
                    if (not is_overlapping(tr, [r for r in placed_rooms if r['id'] != room['id']], padding=0.0)
                            and not is_overlapping(to, [r for r in placed_rooms if r['id'] != other['id']], padding=0.0)):
                        room['x'], room['y'] = tr['x'], tr['y']
                        other['x'], other['y'] = to['x'], to['y']
                        modified = True
                        break
            if modified:
                break
    return placed_rooms


def add_connecting_corridors(rooms, corridor_id_start=9000):
    corridors = []
    corridor_id = corridor_id_start
    corridor_color = room_properties["Corridor"]["color"]
    room_list = [
        r for r in rooms
        if 'x' in r and r['x'] is not None and r['room'] not in ["Plan Size"] and not r.get('is_corridor', False)
    ]
    filled_gaps = set()

    for i in range(len(room_list)):
        for j in range(i + 1, len(room_list)):
            room1 = room_list[i]
            room2 = room_list[j]
            if find_shared_wall(room1, room2):
                continue
            gap, direction = find_min_gap_distance(room1, room2)
            if direction not in ['H', 'V']:
                continue
            if gap < MIN_CONNECT_GAP_FT or gap > CORRIDOR_WIDTH * 3:
                continue

            r1_x1, r1_y1 = room1['x'], room1['y']
            r1_x2, r1_y2 = r1_x1 + room1['width'], r1_y1 + room1['length']
            r2_x1, r2_y1 = room2['x'], room2['y']
            r2_x2, r2_y2 = r2_x1 + room2['width'], r2_y1 + room2['length']
            corridor_room = None

            if direction == 'H':
                oy1, oy2 = max(r1_y1, r2_y1), min(r1_y2, r2_y2)
                overlap = oy2 - oy1
                if overlap < DOOR_WIDTH:
                    continue
                corr_x = r1_x2 if r1_x2 < r2_x1 else r2_x2
                corr_w = r2_x1 - r1_x2 if r1_x2 < r2_x1 else r1_x1 - r2_x2
                corr_y, corr_l = oy1, overlap
                if corr_l > CORRIDOR_WIDTH * 2:
                    cy = oy1 + overlap / 2
                    corr_y, corr_l = cy - CORRIDOR_WIDTH / 2, CORRIDOR_WIDTH
                gk = (round(corr_x, 1), round(corr_y, 1), round(corr_w, 1), round(corr_l, 1))
                if gk in filled_gaps:
                    continue
                filled_gaps.add(gk)
                corridor_room = {
                    "id": corridor_id, "room": "Corridor", "name": "Corridor",
                    "x": round(corr_x, 2), "y": round(corr_y, 2),
                    "width": round(corr_w, 2), "length": round(corr_l, 2),
                    "area_sqft": round(corr_w * corr_l, 2), "color": corridor_color,
                    "is_corridor": True, "door_direction": None, "window_direction": None,
                    "is_entrance": False, "connecting": [room1['room'], room2['room']],
                }

            elif direction == 'V':
                ox1, ox2 = max(r1_x1, r2_x1), min(r1_x2, r2_x2)
                overlap = ox2 - ox1
                if overlap < DOOR_WIDTH:
                    continue
                corr_y = r1_y2 if r1_y2 < r2_y1 else r2_y2
                corr_l = r2_y1 - r1_y2 if r1_y2 < r2_y1 else r1_y1 - r2_y2
                corr_x, corr_w = ox1, overlap
                if corr_w > CORRIDOR_WIDTH * 2:
                    cx = ox1 + overlap / 2
                    corr_x, corr_w = cx - CORRIDOR_WIDTH / 2, CORRIDOR_WIDTH
                gk = (round(corr_x, 1), round(corr_y, 1), round(corr_w, 1), round(corr_l, 1))
                if gk in filled_gaps:
                    continue
                filled_gaps.add(gk)
                corridor_room = {
                    "id": corridor_id, "room": "Corridor", "name": "Corridor",
                    "x": round(corr_x, 2), "y": round(corr_y, 2),
                    "width": round(corr_w, 2), "length": round(corr_l, 2),
                    "area_sqft": round(corr_w * corr_l, 2), "color": corridor_color,
                    "is_corridor": True, "door_direction": None, "window_direction": None,
                    "is_entrance": False, "connecting": [room1['room'], room2['room']],
                }

            if corridor_room:
                corridors.append(corridor_room)
                corridor_id += 1

    return corridors


def place_main_entrance(placed_rooms, main_room, room_id_counter):
    entrance_x = main_room['x'] + main_room['width'] / 2 - MAIN_ENTRANCE_WIDTH / 2
    entrance_y = main_room['y'] - MAIN_ENTRANCE_LENGTH - ROOM_PADDING
    room_id_counter += 1
    main_entrance = {
        "id": room_id_counter, "room": "Main Entrance",
        "length": MAIN_ENTRANCE_LENGTH, "width": MAIN_ENTRANCE_WIDTH,
        "area_sqft": MAIN_ENTRANCE_LENGTH * MAIN_ENTRANCE_WIDTH,
        "x": max(1.0, entrance_x), "y": max(1.0, entrance_y), "is_entrance": True,
    }
    if not is_overlapping(main_entrance, placed_rooms, padding=ROOM_PADDING):
        return main_entrance, room_id_counter
    return None, room_id_counter


def generate_plan(user_rooms_data, plan_id):
    rooms_to_place = []
    room_id_counter = 0
    total_area_sqft = 0

    for room_name, data in user_rooms_data.items():
        count = data.get('count', 1)
        length = data.get('length')
        width = data.get('width')
        if not length or not width or length <= 0 or width <= 0:
            continue
        for _ in range(count):
            room_id_counter += 1
            rd = {"id": room_id_counter, "room": room_name, "length": length, "width": width,
                  "area_sqft": length * width, "x": None, "y": None}
            rooms_to_place.append(rd)
            total_area_sqft += rd["area_sqft"]

    if not rooms_to_place:
        return None

    approx_side = math.sqrt(total_area_sqft)
    MAX_HOUSE_SIZE = max(60.0, approx_side * 1.5)
    rooms_to_place.sort(key=lambda r: r['area_sqft'], reverse=True)

    placed_rooms = []

    # Anchor: Living Room or Family Room
    main_candidates = [r for r in rooms_to_place if r['room'] in ["Living Room", "Family Room"]]
    main_room = main_candidates[0] if main_candidates else rooms_to_place[0]
    rooms_to_place.remove(main_room)
    main_room['x'] = INITIAL_OFFSET
    main_room['y'] = INITIAL_OFFSET
    placed_rooms.append(main_room)

    # Place Kitchen immediately adjacent to Living Room (2nd priority)
    kitchen_room = next((r for r in rooms_to_place if r['room'] == 'Kitchen'), None)
    if kitchen_room:
        rooms_to_place.remove(kitchen_room)
        placed = False
        for side_x, side_y in [
            (main_room['x'] + main_room['width'], main_room['y']),
            (main_room['x'], main_room['y'] + main_room['length']),
            (main_room['x'] - kitchen_room['width'], main_room['y']),
        ]:
            kitchen_room['x'] = max(0.0, side_x)
            kitchen_room['y'] = max(0.0, side_y)
            if not is_overlapping(kitchen_room, placed_rooms, padding=0.0):
                placed_rooms.append(kitchen_room)
                placed = True
                break
        if not placed:
            kitchen_room['x'] = main_room['x'] + main_room['width']
            kitchen_room['y'] = main_room['y']
            placed_rooms.append(kitchen_room)

    # Place remaining rooms
    for new_room in rooms_to_place:
        best_pos = None
        best_score = -float('inf')
        for _ in range(50):
            neighbor = random.choice(placed_rooms)
            side = random.choice(['N', 'S', 'E', 'W'])
            padding_to_use = 0.0 if neighbor['room'] in adjacency_preferences.get(new_room['room'], []) else ROOM_PADDING
            px, py = neighbor['x'], neighbor['y']
            if side == 'N':
                py = neighbor['y'] + neighbor['length'] + padding_to_use
                px += random.uniform(-new_room['width'] * 0.5, neighbor['width'] * 0.5)
            elif side == 'S':
                py = neighbor['y'] - new_room['length'] - padding_to_use
                px += random.uniform(-new_room['width'] * 0.5, neighbor['width'] * 0.5)
            elif side == 'E':
                px = neighbor['x'] + neighbor['width'] + padding_to_use
                py += random.uniform(-new_room['length'] * 0.5, neighbor['length'] * 0.5)
            elif side == 'W':
                px = neighbor['x'] - new_room['width'] - padding_to_use
                py += random.uniform(-new_room['length'] * 0.5, neighbor['length'] * 0.5)

            px = max(0.0, px)
            py = max(0.0, py)
            if px + new_room['width'] > MAX_HOUSE_SIZE + INITIAL_OFFSET or py + new_room['length'] > MAX_HOUSE_SIZE + INITIAL_OFFSET:
                continue
            temp = {**new_room, 'x': px, 'y': py}
            if not is_overlapping(temp, placed_rooms, padding=ROOM_PADDING):
                score = 1 + (10 if neighbor['room'] in adjacency_preferences.get(new_room['room'], []) else 0)
                dist = math.sqrt((px - main_room['x']) ** 2 + (py - main_room['y']) ** 2)
                score += dist * 0.05 if new_room['room'] in ["Kitchen", "Dining Room"] else -dist * 0.05
                if score > best_score:
                    best_score = score
                    best_pos = {'x': px, 'y': py}

        if best_pos:
            new_room['x'] = best_pos['x']
            new_room['y'] = best_pos['y']
            placed_rooms.append(new_room)
        else:
            for _ in range(50):
                rx = random.uniform(0, MAX_HOUSE_SIZE - new_room['width']) + INITIAL_OFFSET / 2
                ry = random.uniform(0, MAX_HOUSE_SIZE - new_room['length']) + INITIAL_OFFSET / 2
                temp = {**new_room, 'x': rx, 'y': ry}
                if not is_overlapping(temp, placed_rooms, padding=ROOM_PADDING):
                    new_room['x'] = rx
                    new_room['y'] = ry
                    placed_rooms.append(new_room)
                    break

    placed_rooms = snap_preferred_adjacent_rooms(placed_rooms)
    placed_rooms = snap_living_room_adjacent(placed_rooms)
    placed_rooms = force_kitchen_near_living_room(placed_rooms)

    main_entrance, room_id_counter = place_main_entrance(placed_rooms, main_room, room_id_counter)
    if main_entrance:
        placed_rooms.append(main_entrance)

    placed_rooms = fit_and_connect_rooms(placed_rooms, main_room['id'])

    corridors = add_connecting_corridors(placed_rooms)
    placed_rooms.extend(corridors)

    # Build final rooms list
    final_rooms = []
    for room in placed_rooms:
        if room.get('x') is None or room.get('y') is None:
            continue
        is_corridor = room.get('is_corridor', False)
        is_entrance = room.get('is_entrance', False)

        if is_corridor:
            props = room_properties.get("Corridor", {})
            name = "Corridor"
            door_dir, window_dir = None, None
        elif is_entrance:
            props = room_properties.get("Main Entrance", {})
            name = "Main Entrance"
            door_dir, window_dir = "S", None
        else:
            props = room_properties.get(room['room'], {})
            name = room['room']
            vd = [d for d in props.get('doors', []) if d]
            vw = [w for w in props.get('windows', []) if w]
            door_dir = random.choice(vd) if vd else None
            window_dir = random.choice(vw) if vw else None

        final_rooms.append({
            "name": name, "room": name, "id": room['id'],
            "x": round(room['x'], 2), "y": round(room['y'], 2),
            "length": round(room['length'], 2), "width": round(room['width'], 2),
            "area_sqft": round(room['area_sqft'], 2),
            "door_direction": door_dir, "window_direction": window_dir,
            "color": props.get('color', '#CCCCCC'),
            "is_corridor": is_corridor, "is_entrance": is_entrance,
            "connecting": room.get('connecting', []),
        })

    if not final_rooms:
        return None

    # Post-processing: add corridors to fix remaining unreachable rooms
    final_rooms_no_plan = [r for r in final_rooms if r['room'] != 'Plan Size']
    add_corridors_for_unreachable(final_rooms_no_plan, final_rooms)

    # Compute bounding box
    all_rooms = final_rooms
    min_x = min(r['x'] for r in all_rooms)
    min_y = min(r['y'] for r in all_rooms)
    max_x = max(r['x'] + r['width'] for r in all_rooms)
    max_y = max(r['y'] + r['length'] for r in all_rooms)

    buffer = 2.0
    min_x -= buffer
    min_y -= buffer
    max_x += buffer
    max_y += buffer

    bba = (max_x - min_x) * (max_y - min_y)
    plan_size_data = {
        "name": "Plan Size", "room": "Plan Size",
        "x": round(min_x, 2), "y": round(min_y, 2),
        "length": round(max_y - min_y, 2), "width": round(max_x - min_x, 2),
        "area_sqft": round(bba, 2), "color": room_properties['Plan Size']['color'],
        "is_open_area": True,
    }

    inter_room_doors = add_inter_room_doors(final_rooms)
    adjacency_map = get_adjacency_map(final_rooms)
    connectivity_check = check_connectivity(final_rooms, adjacency_map)
    design_warnings = check_design_rules(final_rooms, adjacency_map)
    room_gaps = calculate_room_gaps(final_rooms)

    return {
        "name": f"Plan {plan_id}",
        "total_area_sqft": total_area_sqft,
        "rooms": final_rooms,
        "doors": inter_room_doors,
        "plan_size_data": plan_size_data,
        "room_gaps": room_gaps,
        "validation": {"connectivity": connectivity_check, "warnings": design_warnings},
        "boundary": {"min_x": round(min_x, 2), "min_y": round(min_y, 2), "max_x": round(max_x, 2), "max_y": round(max_y, 2)},
    }


@app.route('/add_room_data', methods=['POST'])
def add_room_data():
    data = request.get_json()
    return jsonify({"message": "Room data received successfully", "data": data}), 200


@app.route('/generate_plan', methods=['POST'])
def generate_plan_route():
    data = request.get_json()
    rooms_data = data.get('rooms', {})
    if not rooms_data:
        return jsonify({"error": "No room dimensions provided."}), 400

    generated_plans = []
    for i in range(1, PLAN_COUNT + 1):
        plan = generate_plan(rooms_data, i)
        if plan:
            generated_plans.append(plan)

    if not generated_plans:
        return jsonify({"error": "Failed to generate any floor plans."}), 500

    return jsonify({"plans": generated_plans}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
