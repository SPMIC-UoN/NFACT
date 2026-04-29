import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from matplotlib.patches import Polygon, Circle, Rectangle
from matplotlib import patheffects
from matplotlib.lines import Line2D
import seaborn as sns
from scipy.spatial import ConvexHull, distance_matrix, KDTree, distance
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
        col: str = "magma",
        ring_col: tuple = (0.0, 0.8, 0.0),
        point_size: int = 30,
        hull_lw: float = 1.5,
        label_fontsize: int = 10,
        ring_scale_frac: float = 0.01,
    ) -> None:
        """
        init method to set up class.

        Parameters
        -----------
        proj: np.ndarray
            2D projections.
        labels: np.ndarray
            Cluster labels.
        internal_average: np.ndarray
            internal average cluster statistic.
        centroid_indices: np.ndarray
            Which single estimate is the
            centroid.
        output_dir: str
            output directory to save
            graph to.
        col: str
            Which plt cmap to use.
            Default is magma,
        ring_col: tuple
            What ring colour to use
            default is green
            (0.0, 0.8, 0.0),
        point_size: int
            How big single estimates
            should be. Default is 30.
        label_fontsize: int
            How big the label is. Default is 10.
        ring_scale_frac: float
            How big the centroid ring should be
            Default is 0.01.

        Returns
        --------
        None
        """
        self.proj = proj
        self.labels = labels
        self.internal_average = internal_average
        self.centroid_indices = centroid_indices
        self.output_dir = output_dir
        self.point_size = point_size
        self.hull_lw = hull_lw
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

        self.cmap = plt.get_cmap(col)  # or "inferno", "plasma", "magma"
        self.norm = mcolors.Normalize(
            vmin=np.min(self.internal_average), vmax=np.max(self.internal_average)
        )
        self.min_reliable_size = 5
        self.any_unreliable_clusters = False
        self.ring_col = ring_col

    # ------------------ SETUP ------------------

    def _setup_axis(self) -> None:
        """
        Method to set up axis

        Parameters
        -----------
        None

        Returns
        --------
        None
        """
        self.fig = plt.figure(figsize=(9, 9), facecolor=(0.05, 0.05, 0.05))
        self.ax = self.fig.add_axes([0.02, 0.02, 0.96, 0.96])
        self.ax.set_facecolor((0.05, 0.05, 0.05))
        self.ax.set_xticks([])
        self.ax.set_yticks([])

    def _plot_points(self) -> None:
        """
        Method to plot single estimates

        Parameters
        -----------
        None

        Returns
        --------
        None
        """
        self.ax.scatter(
            self.proj[:, 0],
            self.proj[:, 1],
            s=self.point_size,
            color=(0.20, 0.20, 0.27),
            edgecolor="grey",
            linewidths=0.5,
            zorder=3,
            alpha=0.6,
        )

    # ------------------ SORTING ------------------

    def _compute_cluster_metadata(self) -> list:
        """
        Method to compute hull size and
        data for sorting

        Parameters
        ----------
        None

        Returns
        -------
        list: list object
            list of dictionaries
            containing meta data
        """
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
                    "indices": cluster_indices,
                    "label": lab,
                    "area": area,
                }
            )
        return meta

    def _sorted_metadata(self) -> list:
        """
        Method to order clusters
        by size so smallest are at the front

        Parameters
        -----------
        None

        Returns
        --------
        list: list object
            list of sorted metadata
        """
        return sorted(
            self._compute_cluster_metadata(), key=lambda x: x["area"], reverse=True
        )

    # ------------------ GEOMETRY ------------------

    def _enforce_containment(
        self, cluster_pts: np.ndarray, hull_pts: np.ndarray, max_iter: int = 50
    ) -> np.ndarray:
        """
        Method to ensure all cluster points are contained
        within a convex hull.

        Parameters
        -----------
        cluster_pts: np.ndarray
            cluster points
        hull_pts: np.ndarray
            hull points
        max_iter: int
            Number of iterations
            Default is 50

        Returns
        --------
        np.ndarray: array
            arrray of new cluster points
        """
        for _ in range(max_iter):
            mask = self._convex_contains(cluster_pts, hull_pts)
            if np.all(mask):
                return hull_pts

            centroid = hull_pts.mean(axis=0)
            new_hull = []
            for vertex in hull_pts:
                direction = vertex - centroid
                direction /= np.linalg.norm(direction)
                new_vertex = vertex + direction * 0.01 * np.linalg.norm(
                    vertex - centroid
                )
                new_hull.append(new_vertex)
            hull_pts = np.array(new_hull)
        return cluster_pts[ConvexHull(cluster_pts).vertices]

    def _smooth_closed_curve(
        self, points: np.ndarray, n_points: int = 150, smooth: float = 0.0
    ) -> np.ndarray:
        """
        Function to do  parametric spline
        smoothing of a closed curve

        Parameters
        ----------
        points: np.ndarray
            hull points to smooth
        n_points: int
            number of points to smooth
            Default is 150.
        smooth: float
            smoothing kernel.
            Default is 0.0

        Returns
        -------
        np.ndarray: array
            array of smoothed points
        """
        _, unique_indices = np.unique(points, axis=0, return_index=True)
        points = points[np.sort(unique_indices)]
        if not np.allclose(points[0], points[-1]):
            points = np.vstack([points, points[0]])
        tck, _ = splprep([points[:, 0], points[:, 1]], s=smooth, per=True)
        u_fine = np.linspace(0, 1, n_points)
        x_smooth, y_smooth = splev(u_fine, tck)
        return np.c_[x_smooth, y_smooth]

    def _convex_contains(
        self, points: np.ndarray, polygon: np.ndarray, tol: float = 1e-12
    ) -> np.ndarray:
        """
        Function to check if convex hull contains

        Parameters
        -----------
        points: np.ndarray
            points
        polygon: np.ndarray
            polygon array
        tol: float
            tol to handle
            floating point errors
            Default is 1e-12

        Returns
        -------
        np.ndarray: array

        """
        p2 = np.roll(polygon, -1, axis=0)
        edges = p2 - polygon
        to_points = points[:, None, :] - polygon[None, :, :]
        cross = (
            edges[None, :, 0] * to_points[:, :, 1]
            - edges[None, :, 1] * to_points[:, :, 0]
        )
        cross[np.abs(cross) < tol] = 0
        signs = np.sign(cross)
        all_pos = np.all(signs >= 0, axis=1)
        all_neg = np.all(signs <= 0, axis=1)
        return all_pos | all_neg

    def _get_global_optimal_circular_inflation_params(
        self, all_points: np.ndarray
    ) -> tuple:
        """
        Method to get optimum inflation factors for
        a hull to inflate around the orginal points

        Parameters
        -----------
        all_points: np.ndarray
            all the points

        Returns
        --------
        tuple: tuple[float]
            tuple of optimum
            values
        """

        centroid = all_points.mean(axis=0)
        map_span = np.ptp(all_points, axis=0).max()
        x0_frac = [0.01, 0.02, 0.05]
        x0 = np.array(x0_frac) * map_span

        def objective(params: np.ndarray) -> float:
            """
            Objectivie function to minimse

            Parameters
            -----------
            params: np.ndarray
                parameters to minise

            Returns
            -------
            float: float
                float of the optimised value
            """
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
        cluster_pts: np.ndarray,
        total_cluster_pts: int,
        map_span: float,
        search_radius_parameters: float,
        inflation_buffer_parameter: float,
        radius_parameter: float,
    ) -> np.ndarray:
        """
        Method to inflate the circular convex hull

        Parameters
        ----------
        cluster_pts: np.ndarray,
            cluster points
        total_cluster_pts: int
            total number of cluster points
        map_span: float
            overall spatial scale of your point set
        search_radius_parameters: float
            parameter to search for in the raidus
        inflation_buffer_parameter: float
            What is the buffer on inflation
        radius_parameter: float
            radius parameters

        Returns
        -------
        combined_pts: np.ndarray
            inflated hull points
        """
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
    def _compute_cluster_stats(self, cluster_pts: np.ndarray) -> tuple:
        """
        Method to compute the aspect
        ratio of cluster and the pca of the cluster

        Parameters
        -----------
        cluster_pts: np.ndarray
            cluster points

        Returns
        -------
        tuple: tuple[float, np.ndarray]
            tuple of aspect_ratio and pca
        """
        pca = PCA(n_components=2)
        pca.fit(cluster_pts)
        lengths = np.sqrt(pca.explained_variance_)
        aspect_ratio = lengths[0] / lengths[1] if lengths[1] > 0 else 1.0
        return aspect_ratio, pca

    def _get_hull_metrics(self, points: np.ndarray) -> tuple:
        """
        Method to obtain hull metrics
        of maximum distance between points nad
        minium width

        Parameters
        ----------
        points: np.ndarray
            hull points

        Returns
        -------
        tuple: tuple[float, float]
            tuple of max_dist, min_width
        """
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]

        # 1. Calculate Diameter (Max distance between any two vertices)
        # For small/medium sets, a brute-force search on hull vertices is very fast
        dists = distance.cdist(hull_points, hull_points, "euclidean")
        max_dist = np.max(dists)

        # 2. Calculate Width (Minimum distance between parallel lines touching the hull)
        # This checks the distance from every edge to its furthest vertex
        widths = []
        for point in range(len(hull_points)):
            hull_p1 = hull_points[point]
            hull_p2 = hull_points[(point + 1) % len(hull_points)]
            edge_vec = hull_p2 - hull_p1
            edge_norm = np.linalg.norm(edge_vec)

            # Distance from all other points to this edge line
            # Formula: |(x2-x1)(y1-y0) - (x1-x0)(y2-y1)| / distance(p1, p2)
            diffs = hull_p1 - hull_points
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
        cluster_pts: np.ndarray,
        aspect_ratio: float,
        min_squeeze: float = 1.0,
        max_squeeze: float = 10.0,
        tol: float = 1e-6,
        max_iter: int = 50,
    ):
        """
         Method to squeeze enlogated clusters
        as defined by an aspect ratio

         Parameters
         -----------
         cluster_pts: np.ndarray
             array of cluster points
         aspect_ratio: float
             aspect ratio of cluster
         min_squeeze: float
             minimum squeeze factor.
             Default is 1.0
         max_squeeze: float=10.0
             maximum squeeze factor.
             Default is 10.0
         tol: float
             tol for precision errors
             Default is 1e-6
         max_iter: int
             max number of iterations
             Default is 50
        """
        hull = ConvexHull(cluster_pts)
        hull_pts = cluster_pts[hull.vertices]

        if aspect_ratio < 2.0:
            centroid = np.mean(hull_pts, axis=0)
            return centroid + (hull_pts - centroid) * 1.02

        _, pca = self._compute_cluster_stats(cluster_pts)
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

    def _enforce_min_vertex_distance(
        self, hull_pts: np.ndarray, min_distance: float = 0.1, max_iter: int = 20
    ) -> np.ndarray:
        """
        Ensure that each vertex in the convex hull is at least `min_distance`
        away from its immediate neighbors along the hull.

        Parameters
        ----------
        hull_pts: np.ndarray
            Hull vertices in order.
        min_distance : float
            Minimum allowed distance between
            consecutive vertices. Default is 0.1
        max_iter : int
            Maximum iterations to relax the hull.
            Default is 20

        Returns
        -------
        hull_pts: np.ndarray array
            Adjusted hull vertices
            satisfying minimum distance constraint.
        """
        hull_length = len(hull_pts)
        avg_edge_length = np.mean(
            [
                np.linalg.norm(
                    hull_pts[hull_point] - hull_pts[(hull_point + 1) % hull_length]
                )
                for hull_point in range(hull_length)
            ]
        )
        max_step = 0.2 * avg_edge_length
        for _ in range(max_iter):
            centroid = np.mean(hull_pts, axis=0)
            moved = False

            for index in range(hull_length):
                hull_point = hull_pts[index]
                prev_point = hull_pts[(index - 1) % hull_length]
                next_point = hull_pts[(index + 1) % hull_length]

                # distance to neighbors
                distance_prev = np.linalg.norm(hull_point - prev_point)
                distance_next = np.linalg.norm(hull_point - next_point)

                # only inflate if below threshold
                for point_distance, _ in zip(
                    [distance_prev, distance_next], [prev_point, next_point]
                ):
                    excess_needed = (
                        min_distance - point_distance
                    )  # how much we need to expand
                    vertex_step = np.clip(excess_needed * 0.5, 0, max_step)
                    if point_distance < min_distance:
                        # direction from centroid to vertex
                        point_distance = hull_point - centroid
                        direction_norm = np.linalg.norm(point_distance)
                        if direction_norm > 0:
                            point_distance /= direction_norm
                            # nudge by a small step
                            hull_pts[index] += point_distance * vertex_step
                            moved = True

            if not moved:
                break
        return hull_pts

    def _ring_radius(self) -> None:
        """
        Method to set centroid ring
        radius

        Parameters
        ----------
        None

        Returns
        --------
        None
        """
        data_range = np.ptp(self.proj, axis=0)
        self.uniform_radius = np.max(data_range) * self.ring_scale_frac

    def _build_hull(self, pts: np.ndarray) -> np.ndarray:
        """
        Method to build intial hull

        Parameters
        ----------
        pts: np.ndarray
            cluster points

        Returns
        --------
        pts: np.ndarray
            hull points
        """
        hull = ConvexHull(pts)
        return pts[hull.vertices]

    # ------------------ DRAWING ------------------

    def _add_core_hull(self, hull_smooth: np.ndarray, colour: np.ndarray) -> None:
        """
        Method to add core hull
        to graph.

        Parameters
        -----------
        hull_smooth: np.ndarray
            pre-processed hull
            points
        colour: np.ndarray
            colour of hull
            RGB

        Returns
        --------
        None
        """
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

    def _add_label(self, centroid_pos: int, lab: int) -> None:
        """
        Method to add cluster number to plot

        Parameters
        ----------
        centroid_pos: int
            centroid position
        lab: int
            cluster label

        Returns
        -------
        None
        """
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

    def _add_centroid_circle(self, centroid_pos: int) -> None:
        """
        Method to add centroid ring to plot

        Parameters
        ----------
        centroid_pos: int
            centroid position


        Returns
        -------
        None
        """
        ring = Circle(
            centroid_pos,
            radius=self.uniform_radius,
            edgecolor=self.ring_col,
            facecolor="none",
            linewidth=2,
            zorder=5,
        )
        self.ax.add_patch(ring)

    # ------------------ MAIN LOOP ------------------
    def _plot_clusters(self) -> np.ndarray:
        """
        Method to plot clusters

        Parameters
        -----------
        cluster_idx: np.ndarray
            cluster index

        Returns
        -------
        all_points: np.ndarray
            array of all hull points
        """
        map_span = np.ptp(self.proj, axis=0).max()

        (search_radius_parameters, inflation_buffer_parameter, radius_parameter) = (
            self._get_global_optimal_circular_inflation_params(self.proj)
        )
        all_points = []
        for meta in self._sorted_metadata():
            index = meta["indices"]
            lab = meta["label"]
            cluster_position = self.label_to_position[lab]
            cluster_proj = self.proj[index]
            centroid_pos = self.centroids[cluster_position]
            if len(cluster_proj) < self.min_reliable_size:
                self._add_unreliable_square(centroid_pos)
                self._add_label(centroid_pos, lab)
                self.any_unreliable_clusters = True
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

            smooth_hull = self._smooth_closed_curve(
                hull_pts, n_points=150, smooth=0.005
            )
            all_points.append(smooth_hull)

            cluster_stat = self.internal_average[cluster_position]
            colour = self.cmap(self.norm(cluster_stat))

            self._add_core_hull(smooth_hull, colour)
            self._add_label(centroid_pos, lab)
            self._add_centroid_circle(centroid_pos)

        return all_points

    # ------------------ FINAL LAYOUT ------------------

    def _add_padding(self, all_points: np.ndarray) -> None:
        """
        Method to add padding to plot so that
        clusters are not overlapping with frame

        Parameters
        -----------
        all_points: np.ndarray
            array of all hull points

        Returns
        -------
        None
        """
        if not all_points:
            return
        all_pts_arr = np.vstack(all_points)
        x_min, y_min = all_pts_arr.min(axis=0)
        x_max, y_max = all_pts_arr.max(axis=0)
        x_range = x_max - x_min
        y_range = y_max - y_min
        padding = 0.009
        self.ax.set_xlim(x_min - x_range * padding, x_max + x_range * padding)
        self.ax.set_ylim(y_min - y_range * padding, y_max + y_range * padding)

    def _clear_axes(self) -> None:
        """
        Method to clear axis of not needed
        information

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.set_aspect("equal", adjustable="box")

    # ------------------ EXTRAS ------------------

    def _add_rects(self) -> None:
        """
        Method to add frame to plot

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
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

    def _add_colourbar(self) -> None:
        """
        Method to add colour bar
        and text

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        sm = cm.ScalarMappable(cmap=self.cmap, norm=self.norm)
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
        """
        Method to add plot legend

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        legend_elements = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                label="Centroid",
                markerfacecolor="none",
                markeredgecolor=self.ring_col,
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

        if self.any_unreliable_clusters:
            legend_elements.append(
                Line2D(
                    [0],
                    [0],
                    marker="s",
                    color="none",
                    label="Unreliable Cluster",
                    markerfacecolor="none",
                    markeredgecolor=(1.0, 0.2, 0.2),
                    markersize=10,
                    markeredgewidth=2,
                ),
            )

        leg = self.ax.legend(
            handles=legend_elements,
            loc="upper right",
            facecolor=(0.05, 0.05, 0.05),
            edgecolor=(0.5, 0.5, 0.5),
            fontsize=9,
            framealpha=1,
        )
        plt.setp(leg.get_texts(), color="w")

    def _add_title(self) -> None:
        """
        Method to add plot title

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.ax.set_title(
            "Estimated space as a 2D CCA Projection",
            color="white",
            fontsize=14,
            pad=20,
        )

    def _add_unreliable_square(self, centroid_pos: np.ndarray) -> None:
        """
        Draw a red square around unreliable cluster centroid.

        Parameters
        ----------
        centroid_pos : np.ndarray
            x, y centroid position
        size_frac : float
            fraction of map span used as square size
        """

        half_size = self.uniform_radius
        square = Rectangle(
            (centroid_pos[0] - half_size, centroid_pos[1] - half_size),
            width=half_size * 2,
            height=half_size * 2,
            fill=False,
            edgecolor=(1.0, 0.2, 0.2),
            linewidth=2.5,
            linestyle="-",
            zorder=9,
        )

        self.ax.add_patch(square)

    # ------------------ PUBLIC API ------------------

    def plot(self) -> None:
        """
        Main plotting method.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self._setup_axis()
        self._plot_points()
        self._ring_radius()
        all_points = self._plot_clusters()
        self._add_padding(all_points)
        self._clear_axes()
        self._add_colourbar()
        self._add_rects()
        self._add_legend()
        self._add_title()
        plt.savefig(self.output_dir, format="tiff", dpi=300, bbox_inches="tight")
        plt.close(self.fig)


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
    step = max(1, round(clusters_scores["clusternumber"].shape[0] / 100 * 10))
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
