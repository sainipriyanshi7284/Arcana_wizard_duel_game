import math

def check_circle_collision(x1, y1, r1, x2, y2, r2):
    """
    Returns True if two circles overlap.
    """
    dist_sq = (x2 - x1)**2 + (y2 - y1)**2
    radius_sum_sq = (r1 + r2)**2
    return dist_sq <= radius_sum_sq

def check_point_circle_collision(px, py, cx, cy, r):
    """
    Returns True if a point is inside a circle.
    """
    dist_sq = (cx - px)**2 + (cy - py)**2
    return dist_sq <= (r**2)
