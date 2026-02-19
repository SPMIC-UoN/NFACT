import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from matplotlib.patches import Polygon, Circle, Rectangle
from matplotlib import patheffects
from matplotlib.lines import Line2D
import seaborn as sns
from scipy.spatial import ConvexHull, distance_matrix, KDTree
from scipy.interpolate import splprep, splev
from scipy.optimize import minimize
from sklearn.decomposition import PCA
import numpy as np


class NMFgraph:
    """
    Class to plot NMF clusters

    Usage
    -----
    graph = NMFgraph(
            projects,
            cluster_labels,
            stats['internal']['avg'],
            centroids)
    graph.plot()
    """

    def __init__(
        self,
        proj: np.ndarray,
        labels: np.ndarray,
        internal_average: np.ndarray,
        centroid_indices: np.ndarray,
        output_dir: str,
        hull_size: float = 0.2,
        point_size: int = 30,
        hull_lw: float = 1.5,
        alpha_fill: float = 1,
        label_fontsize: int = 10,
        ring_scale_frac: float = 0.01,
    ):
        self.proj = proj
        self.labels = labels
        self.internal_average = internal_average
        self.centroid_indices = centroid_indices
        self.output_dir = output_dir
        self.hull_size = hull_size
        self.point_size = point_size
        self.hull_lw = hull_lw
        self.alpha_fill = alpha_fill
        self.label_fontsize = label_fontsize
        self.ring_scale_frac = ring_scale_frac
        self.unique_labels = np.unique(self.labels)
        self.label_to_position = {
            lab: pos for pos, lab in enumerate(self.unique_labels)
        }
        # --- Precompute static data ---
        self.percentiles = [25, 50, 75, 90]
        self.thresholds = np.percentile(self.internal_average, self.percentiles)
        self.centroids = self.proj[self.centroid_indices]
        self.dist_mat = distance_matrix(self.centroids, self.centroids)

        # Must match function exactly
        self.colours = self._red_colormap(5, 1, 0.8)

    # ------------------ SETUP ------------------

    def _setup_axis(self):
        self.fig = plt.figure(figsize=(9, 9), facecolor=(0.05, 0.05, 0.05))
        self.ax = self.fig.add_axes([0.02, 0.02, 0.96, 0.96])
        self.ax.set_facecolor((0.05, 0.05, 0.05))
        self.ax.set_xticks([])
        self.ax.set_yticks([])

    def _plot_points(self):
        self.ax.scatter(
            self.proj[:, 0],
            self.proj[:, 1],
            s=self.point_size,
            color=(0.20, 0.17, 0.27),
            edgecolor="grey",
            linewidths=0.5,
            zorder=3,
            alpha=0.6,
        )

    # ------------------ COLOUR LOGIC ------------------
    def _red_colormap(
        self, numb_colours: int, red_intensity: float = 1.0, gamma: float = 0.1
    ) -> np.ndarray:
        """
        Function to get red map colouring

        Parameters
        ----------
        numb_colours: int
           number of red shades
        red_intensity: float
           red colour intensity
           default is 1.0
        gamma: float
            scaling factor
            default is 0.1

        Returns
        -------
        cmap: np.ndarray
            colour maps
        """
        cmap = np.zeros((numb_colours, 3))
        cmap[:, 0] = np.linspace(1, red_intensity**2, numb_colours)
        cmap[:, 1] = np.linspace(1, 0, numb_colours)
        cmap[:, 2] = cmap[:, 1]
        cmap = cmap**gamma
        return cmap.astype(np.float32)

    def _set_cluster_colours(self):
        # EXACT function logic
        cluster_color_idx = np.zeros(len(self.internal_average), dtype=int)
        for i, val in enumerate(self.internal_average):
            if val <= self.thresholds[0]:
                cluster_color_idx[i] = 1
            elif val <= self.thresholds[1]:
                cluster_color_idx[i] = 2
            elif val <= self.thresholds[2]:
                cluster_color_idx[i] = 3
            else:
                cluster_color_idx[i] = 4
        return cluster_color_idx

    # ------------------ SORTING ------------------

    def _compute_cluster_metadata(self):
        unique_labels = np.unique(self.labels)
        meta = []

        for lab in unique_labels:
            cluster_indices = np.where(self.labels == lab)[0]
            pts = self.proj[cluster_indices]

            if pts.shape[0] >= 3:
                hull = ConvexHull(pts)
                area = hull.area
            else:
                area = 0.0

            meta.append(
                {
                    "indices": cluster_indices,  # ← FIX: store array of indices
                    "label": lab,
                    "area": area,
                }
            )

        return meta

    def _sorted_metadata(self):
        return sorted(
            self._compute_cluster_metadata(), key=lambda x: x["area"], reverse=True
        )

    # ------------------ GEOMETRY ------------------

    def _enforce_containment(self, cluster_pts, hull_pts, max_iter=50):
        for _ in range(max_iter):
            mask = self._convex_contains(cluster_pts, hull_pts)
            if np.all(mask):
                return hull_pts
            centroid = hull_pts.mean(axis=0)
            new_hull = []

            for v in hull_pts:
                direction = v - centroid
                direction /= np.linalg.norm(direction)
                new_v = v + direction * 0.01 * np.linalg.norm(v - centroid)
                new_hull.append(new_v)
            hull_pts = np.array(new_hull)
        return cluster_pts[ConvexHull(cluster_pts).vertices]

    def _smooth_closed_curve(self, points, n_points=150, s=0.0):
        points = np.array(points)

        _, unique_indices = np.unique(points, axis=0, return_index=True)

        points = points[np.sort(unique_indices)]
        if not np.allclose(points[0], points[-1]):
            points = np.vstack([points, points[0]])

        tck, u = splprep([points[:, 0], points[:, 1]], s=s, per=True)

        u_fine = np.linspace(0, 1, n_points)
        x_smooth, y_smooth = splev(u_fine, tck)
        return np.c_[x_smooth, y_smooth]

    def _convex_contains(self, points, polygon, tol=1e-12):
        polygon = np.asarray(polygon)
        points = np.asarray(points)
        n = len(polygon)
        inside = []
        for p in points:
            sign = None
            is_inside = True
            for i in range(n):
                a = polygon[i]
                b = polygon[(i + 1) % n]
                edge = b - a
                to_point = p - a
                cross = edge[0] * to_point[1] - edge[1] * to_point[0]
                if abs(cross) < tol:
                    continue
                current_sign = np.sign(cross)
                if sign is None:
                    sign = current_sign
                elif current_sign != sign:
                    is_inside = False
                    break

            inside.append(is_inside)
        return np.array(inside)

    def _get_global_optimal_circular_inflation_params(self, all_points):
        all_points = np.array(all_points)

        centroid = all_points.mean(axis=0)

        # map span
        map_span = np.ptp(all_points, axis=0).max()

        # initial guess as fractions of map span
        x0_frac = [0.01, 0.02, 0.05]

        # convert to coordinate units
        x0 = np.array(x0_frac) * map_span

        def objective(params):
            search_radius, inflation_buffer, radius_param = params
            search_radius = max(search_radius, 1e-6)
            inflation_buffer = max(inflation_buffer, 1e-6)
            radius_param = max(radius_param, 1e-6)
            radial_dists = np.linalg.norm(all_points - centroid, axis=1)

            if len(all_points) > 3:
                radius = np.median(radial_dists) + inflation_buffer
            else:
                radius = radius_param

            angles = np.linspace(0, 2 * np.pi, 24)

            circle_pts = centroid + np.c_[np.cos(angles), np.sin(angles)] * radius

            combined_pts = np.vstack([all_points, circle_pts])
            hull = ConvexHull(combined_pts)
            hull_pts = combined_pts[hull.vertices]

            # ensure containment
            mask = self._convex_contains(all_points, hull_pts)

            if not np.all(mask):
                return 1e6

            max_extra = (
                np.max(np.linalg.norm(hull_pts - centroid, axis=1))
                - np.max(radial_dists)
            ) / map_span

            return max_extra

        bounds = [
            (0.001 * map_span, 0.1 * map_span),
            (0.001 * map_span, 0.05 * map_span),
            (0.001 * map_span, 0.1 * map_span),
        ]

        res = minimize(objective, x0, bounds=bounds, method="L-BFGS-B")

        optimal_frac = res.x / map_span
        return optimal_frac

    def _get_circular_inflation(
        self,
        cluster_pts,
        total_cluster_pts,
        map_span,
        search_radius_parameters,
        inflation_buffer_parameter,
        radius_parameter,
    ):
        hotspot_center = np.mean(cluster_pts, axis=0)

        internal_distances = np.linalg.norm(cluster_pts - hotspot_center, axis=1)

        avg_internal_dist = np.mean(internal_distances)

        tree = KDTree(cluster_pts)

        search_radius = map_span * search_radius_parameters

        local_count = len(tree.query_ball_point(hotspot_center, r=search_radius))

        density_ratio = local_count / total_cluster_pts

        if local_count > 3:
            inflation_buffer = map_span * inflation_buffer_parameter * density_ratio

            radius = avg_internal_dist + inflation_buffer

        else:
            radius = avg_internal_dist * radius_parameter

        angles = np.linspace(0, 2 * np.pi, 24)

        circle_pts = hotspot_center + np.c_[np.cos(angles), np.sin(angles)] * radius

        combined_pts = np.vstack([cluster_pts, circle_pts])

        hull = ConvexHull(combined_pts)

        return combined_pts[hull.vertices]

    # -----------------------------
    # Compute aspect ratio
    # -----------------------------
    def _compute_cluster_stats(self, cluster_pts):
        pca = PCA(n_components=2)
        pca.fit(cluster_pts)
        lengths = np.sqrt(pca.explained_variance_)
        aspect_ratio = lengths[0] / lengths[1] if lengths[1] > 0 else 1.0
        return aspect_ratio, pca

    def _get_hull_metrics(self, points):
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]

        # 1. Calculate Diameter (Max distance between any two vertices)
        # For small/medium sets, a brute-force search on hull vertices is very fast
        dists = distance.cdist(hull_points, hull_points, "euclidean")
        max_dist = np.max(dists)

        # 2. Calculate Width (Minimum distance between parallel lines touching the hull)
        # This checks the distance from every edge to its furthest vertex
        widths = []
        for i in range(len(hull_points)):
            p1 = hull_points[i]
            p2 = hull_points[(i + 1) % len(hull_points)]

            # Vector for the edge
            edge_vec = p2 - p1
            edge_norm = np.linalg.norm(edge_vec)

            # Distance from all other points to this edge line
            # Formula: |(x2-x1)(y1-y0) - (x1-x0)(y2-y1)| / distance(p1, p2)
            diffs = p1 - hull_points
            cross_2d = edge_vec[0] * diffs[:, 1] - edge_vec[1] * diffs[:, 0]
            dist_to_edge = np.abs(cross_2d) / edge_norm
            widths.append(np.max(dist_to_edge))

        min_width = np.min(widths)

        return max_dist, min_width

    # -----------------------------
    # Directional hull binary search
    # -----------------------------
    def _get_tight_directional_hull_binary_search(
        self,
        cluster_pts,
        aspect_ratio,
        min_squeeze=1,
        max_squeeze=10.0,
        tol=1e-6,
        max_iter=50,
    ):
        hull = ConvexHull(cluster_pts)
        hull_pts = cluster_pts[hull.vertices]

        if aspect_ratio < 2.0:
            centroid = np.mean(hull_pts, axis=0)
            return centroid + (hull_pts - centroid) * 1.02

        aspect_ratio, pca = self._compute_cluster_stats(cluster_pts)
        minor_axis = pca.components_[1]
        centroid = np.mean(cluster_pts, axis=0)
        low = min_squeeze
        high = max_squeeze
        best_hull = hull_pts.copy()

        for _ in range(max_iter):
            mid = (low + high) / 2
            centered = hull_pts - centroid
            dist_from_spine = centered @ minor_axis
            candidate = centered - np.outer((1 - mid) * dist_from_spine, minor_axis)

            candidate += centroid
            mask = self._convex_contains(cluster_pts, candidate)
            if np.all(mask):
                best_hull = candidate
                high = mid
            else:
                low = mid

            if abs(high - low) < tol:
                break

        return best_hull

    def _enforce_min_vertex_distance(self, hull_pts, min_distance=0.1, max_iter=20):
        """
        Ensure that each vertex in the convex hull is at least `min_distance`
        away from its immediate neighbors along the hull.

        Parameters
        ----------
        hull_pts : (N,2) array
            Hull vertices in order.
        min_distance : float
            Minimum allowed distance between consecutive vertices.
        max_iter : int
            Maximum iterations to relax the hull.

        Returns
        -------
        hull_pts : (N,2) array
            Adjusted hull vertices satisfying minimum distance constraint.
        """
        hull_pts = np.array(hull_pts)
        N = len(hull_pts)
        avg_edge_length = np.mean(
            [np.linalg.norm(hull_pts[i] - hull_pts[(i + 1) % N]) for i in range(N)]
        )
        max_step = 0.2 * avg_edge_length
        for _ in range(max_iter):
            centroid = np.mean(hull_pts, axis=0)
            moved = False

            for i in range(N):
                v = hull_pts[i]
                prev_v = hull_pts[(i - 1) % N]
                next_v = hull_pts[(i + 1) % N]

                # distance to neighbors
                d_prev = np.linalg.norm(v - prev_v)
                d_next = np.linalg.norm(v - next_v)

                # only inflate if below threshold
                for d, neighbor in zip([d_prev, d_next], [prev_v, next_v]):
                    excess_needed = min_distance - d  # how much we need to expand
                    vertex_step = np.clip(excess_needed * 0.5, 0, max_step)
                    if d < min_distance:
                        # direction from centroid to vertex
                        direction = v - centroid
                        direction_norm = np.linalg.norm(direction)
                        if direction_norm > 0:
                            direction /= direction_norm
                            # nudge by a small step
                            hull_pts[i] += direction * vertex_step
                            moved = True

            if not moved:
                break
        return hull_pts

    def _ring_radius(self):
        data_range = np.ptp(self.proj, axis=0)
        self.uniform_radius = np.max(data_range) * self.ring_scale_frac

    def _build_hull(self, pts):
        hull = ConvexHull(pts)
        return pts[hull.vertices]

    # ------------------ DRAWING ------------------

    def _add_core_hull(self, hull_smooth, colour):
        core_poly = Polygon(
            hull_smooth,
            closed=True,
            facecolor=colour,
            alpha=0.8,
            edgecolor="grey",
            linewidth=self.hull_lw,
            zorder=2,
        )
        self.ax.add_patch(core_poly)

    def _add_label(self, centroid_pos, lab):
        txt = self.ax.text(
            centroid_pos[0],
            centroid_pos[1],
            str(lab),
            color="white",
            fontsize=self.label_fontsize,
            fontweight="black",
            ha="left",
            va="bottom",
            zorder=10,
        )
        txt.set_path_effects(
            [patheffects.withStroke(linewidth=3, foreground=(0, 0, 0, 0.7))]
        )

    def _add_centroid_circle(self, centroid_pos):
        ring = Circle(
            centroid_pos,
            radius=self.uniform_radius,
            edgecolor=[0.5, 0.5, 0],
            facecolor="none",
            linewidth=2,
            zorder=5,
        )
        self.ax.add_patch(ring)

    # ------------------ MAIN LOOP ------------------
    def _plot_clusters(self, cluster_idx):
        map_span = np.ptp(self.proj, axis=0).max()

        (search_radius_parameters, inflation_buffer_parameter, radius_parameter) = (
            self._get_global_optimal_circular_inflation_params(self.proj)
        )
        all_points = []
        for meta in self._sorted_metadata():
            index = meta["indices"]
            lab = meta["label"]

            cluster_proj = self.proj[index]
            if len(cluster_proj) < 5:
                continue
            ratio, _ = self._compute_cluster_stats(cluster_proj)

            inflated_pts = self._get_circular_inflation(
                cluster_proj,
                len(cluster_proj),
                map_span,
                search_radius_parameters,
                inflation_buffer_parameter,
                radius_parameter,
            )

            hull_pts = self._get_tight_directional_hull_binary_search(
                inflated_pts, ratio
            )

            hull_pts = self._enforce_containment(cluster_proj, hull_pts)
            hull_pts = self._enforce_min_vertex_distance(
                hull_pts, min_distance=0.15, max_iter=10
            )

            smooth_hull = self._smooth_closed_curve(hull_pts, n_points=150, s=0.005)
            all_points.append(smooth_hull)
            cluster_position = self.label_to_position[lab]
            colour = self.colours[cluster_idx[cluster_position]]
            centroid_pos = self.centroids[cluster_position]
            self._add_core_hull(smooth_hull, colour)
            self._add_label(centroid_pos, lab)
            self._add_centroid_circle(centroid_pos)

        return all_points

    # ------------------ FINAL LAYOUT ------------------

    def _add_padding(self, all_points):
        if not all_points:
            return
        all_pts_arr = np.vstack(all_points)
        x_min, y_min = all_pts_arr.min(axis=0)
        x_max, y_max = all_pts_arr.max(axis=0)
        x_range = x_max - x_min
        y_range = y_max - y_min
        padding = 0.05
        self.ax.set_xlim(x_min - x_range * padding, x_max + x_range * padding)
        self.ax.set_ylim(y_min - y_range * padding, y_max + y_range * padding)

    def _clear_axes(self):
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.set_aspect("equal", adjustable="box")

    # ------------------ EXTRAS ------------------

    def _add_rects(self):
        rect = Rectangle(
            (0, 0),
            1,
            1,
            linewidth=4,
            edgecolor="white",
            facecolor="none",
            transform=self.ax.transAxes,
            zorder=4,
        )
        self.ax.add_patch(rect)

        panel = Rectangle(
            (0, 0),
            1,
            1,
            transform=self.fig.transFigure,
            facecolor=(0.1, 0.1, 0.1),
            edgecolor="none",
            zorder=-200,
        )
        self.fig.add_artist(panel)

    def _add_colourbar(self):
        cmap = mcolors.ListedColormap(self.colours[1:5])
        bounds = self.thresholds.tolist()
        bounds[0] = self.internal_average.min()
        bounds[-1] = self.internal_average.max()
        bounds = np.round(bounds, 2)

        norm = mcolors.BoundaryNorm(bounds, cmap.N + 1, clip=False)
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        cbar = plt.colorbar(
            sm,
            ax=self.ax,
            fraction=0.03,
            pad=0.05,
            extend="neither",
            shrink=1.0,
            aspect=25,
        )
        cbar.outline.set_edgecolor((0.7, 0.7, 0.7))
        cbar.outline.set_linewidth(1.0)
        cbar.ax.set_facecolor((0.1, 0.1, 0.1))
        cbar.set_label(
            "Average Intra-cluster similairty (cluster compactness)",
            color="white",
            fontsize=8,
        )
        cbar.ax.yaxis.set_tick_params(color="white", labelcolor="white")
        cbar.ax.text(
            -0.6,
            0.5,
            "Conex hulls represent cluster estimates",
            color="white",
            fontsize=8,
            ha="right",  # Horizontal alignment
            va="center",  # Vertical alignment
            rotation=90,  # Vertical orientation
            transform=cbar.ax.transAxes,
        )
        cbar.ax.text(
            -0.3,
            0.5,
            "Compact and Isolated clusters suggest reliable estimates",
            transform=cbar.ax.transAxes,
            color="white",
            fontsize=8,
            rotation=90,
            ha="center",  # This ensures the text is centered on x_center_spot
            va="center",
        )
        plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="white")

    def _add_legend(self):
        legend_elements = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                label="Centroid",
                markerfacecolor="none",
                markeredgecolor=[0.5, 0.5, 0],
                markersize=10,
                markeredgewidth=2,
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                label="Single Run Estimate",
                markerfacecolor=(0.30, 0.25, 0.40),
                markeredgecolor="grey",
                markersize=8,
                markeredgewidth=0.5,
            ),
        ]

        leg = self.ax.legend(
            handles=legend_elements,
            loc="upper right",
            facecolor=(0.05, 0.05, 0.05),
            edgecolor=(0.5, 0.5, 0.5),
            fontsize=9,
            framealpha=1,
        )
        plt.setp(leg.get_texts(), color="w")

    def _add_title(self):
        self.ax.set_title(
            "Estimated space as a 2D UMAP Projection",
            color="white",
            fontsize=14,
            pad=20,
        )

    # ------------------ PUBLIC API ------------------

    def plot(self):
        self._setup_axis()
        self._plot_points()

        cluster_idx = self._set_cluster_colours()
        self._ring_radius()

        all_points = self._plot_clusters(cluster_idx)

        self._add_padding(all_points)
        self._clear_axes()
        self._add_colourbar()
        self._add_rects()
        self._add_legend()
        self._add_title()
        plt.savefig(self.output_dir, format="tiff", dpi=300, bbox_inches="tight")
        plt.close()


def plot_matrix(file_path: str, mat: np.ndarray, title: str) -> None:
    """
    Function to plot matrix and save
    to file

    Parameters
    ----------
    file_path: str
        file path to save graph to.
        Must include file name
    mat: np.ndarray
        matrix to plot
    title: str
        title of graph

    Returns
    -------
    None
    """
    ax = sns.heatmap(mat, xticklabels="", yticklabels="")
    ax.set_title(title)
    plt.savefig(file_path, format="tiff", dpi=300, bbox_inches="tight")
    plt.close()


def plot_cluster_stats(
    clusters_scores: dict,
    filepath: str,
) -> None:
    """
    Function to plot cluster stats

    Parameters
    ----------
    clusters_scores: dict
       dictionary of cluster
       statilbity scores
    filepath: str
        file path to save graph to.
        Must include file name

    Returns
    --------
    None
    """
    plt.style.use("bmh")
    plt.figure(2)
    step = round(clusters_scores["clusternumber"].shape[0] / 100 * 10)
    y_pos = np.arange(len(clusters_scores["clusternumber"]))
    position = list(y_pos[::step])
    if y_pos[-1] not in position:
        position.append(y_pos[-1])

    labels = [str(clust) for clust in clusters_scores["clusternumber"][::step]]
    if (
        clusters_scores["clusternumber"][-1]
        not in clusters_scores["clusternumber"][::step]
    ):
        labels.append(str(clusters_scores["clusternumber"][-1]))

    plt.figure(figsize=(10, 7))
    plt.clf()
    plt.subplot(1, 2, 1)

    plt.plot(clusters_scores["internal_score"], "o-")
    plt.xticks(position, labels)
    plt.title("Stability Score (Ranked Descending)")
    plt.xlabel("Cluster")
    plt.ylabel("Stablilty Score")
    plt.subplot(1, 2, 2)
    plt.barh(y_pos, np.array(clusters_scores["number_in_cluster"]), align="center")
    plt.gca().invert_yaxis()
    plt.yticks(position, labels)
    plt.xlim(0, max(clusters_scores["number_in_cluster"]) * 1.05)
    plt.title("Number of Components in Clusters (Ranked by Stability)")
    plt.xlabel("Number of Components in Clusters")
    plt.ylabel("Cluster")
    plt.suptitle("Cluster Ranking", fontsize=16, fontweight="bold")
    plt.gcf().canvas.manager.set_window_title("Cluster Ranking")
    plt.tight_layout()
    plt.savefig(filepath, format="tiff", dpi=300, bbox_inches="tight")
    plt.close()
