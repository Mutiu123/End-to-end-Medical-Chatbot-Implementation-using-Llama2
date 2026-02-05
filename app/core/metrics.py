"""
Prometheus Metrics Module

Provides comprehensive metrics collection including:
- Request counters and latencies
- LLM inference metrics
- Database connection metrics
- Custom business metrics
"""

from typing import Callable, Optional

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

from app.core.config import settings


class MetricsCollector:
    """
    Centralized Prometheus metrics collector.

    Provides 15+ metric types for comprehensive monitoring.
    """

    def __init__(self, prefix: str = None, registry: CollectorRegistry = None):
        """
        Initialize metrics collector.

        Args:
            prefix: Metric name prefix
            registry: Optional custom registry
        """
        self.prefix = prefix or settings.metrics_prefix
        self.registry = registry or CollectorRegistry()

        self._init_info_metrics()
        self._init_request_metrics()
        self._init_llm_metrics()
        self._init_database_metrics()
        self._init_auth_metrics()
        self._init_business_metrics()
        self._init_system_metrics()

    def _metric_name(self, name: str) -> str:
        """Generate full metric name with prefix."""
        return f"{self.prefix}_{name}"

    def _init_info_metrics(self) -> None:
        """Initialize application info metrics."""
        self.app_info = Info(
            self._metric_name("app_info"),
            "Application information",
            registry=self.registry,
        )
        self.app_info.info({
            "version": settings.app_version,
            "environment": settings.environment.value,
        })

    def _init_request_metrics(self) -> None:
        """Initialize HTTP request metrics."""
        # Request counter
        self.requests_total = Counter(
            self._metric_name("requests_total"),
            "Total number of HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        # Request latency histogram
        self.request_latency = Histogram(
            self._metric_name("request_latency_seconds"),
            "HTTP request latency in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry,
        )

        # Active requests gauge
        self.active_requests = Gauge(
            self._metric_name("active_requests"),
            "Number of currently active requests",
            ["method", "endpoint"],
            registry=self.registry,
        )

        # Request size histogram
        self.request_size = Histogram(
            self._metric_name("request_size_bytes"),
            "HTTP request size in bytes",
            ["method", "endpoint"],
            buckets=[100, 500, 1000, 5000, 10000, 50000, 100000],
            registry=self.registry,
        )

        # Response size histogram
        self.response_size = Histogram(
            self._metric_name("response_size_bytes"),
            "HTTP response size in bytes",
            ["method", "endpoint"],
            buckets=[100, 500, 1000, 5000, 10000, 50000, 100000],
            registry=self.registry,
        )

    def _init_llm_metrics(self) -> None:
        """Initialize LLM-related metrics."""
        # LLM inference latency
        self.llm_inference_latency = Histogram(
            self._metric_name("llm_inference_latency_seconds"),
            "LLM inference latency in seconds",
            ["model", "operation"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry,
        )

        # LLM requests counter
        self.llm_requests_total = Counter(
            self._metric_name("llm_requests_total"),
            "Total number of LLM requests",
            ["model", "status"],
            registry=self.registry,
        )

        # Token usage counter
        self.llm_tokens_total = Counter(
            self._metric_name("llm_tokens_total"),
            "Total number of tokens processed",
            ["model", "token_type"],
            registry=self.registry,
        )

        # LLM errors counter
        self.llm_errors_total = Counter(
            self._metric_name("llm_errors_total"),
            "Total number of LLM errors",
            ["model", "error_type"],
            registry=self.registry,
        )

    def _init_database_metrics(self) -> None:
        """Initialize database metrics."""
        # Connection pool gauge
        self.db_connections = Gauge(
            self._metric_name("db_connections"),
            "Number of database connections",
            ["state"],
            registry=self.registry,
        )

        # Query latency histogram
        self.db_query_latency = Histogram(
            self._metric_name("db_query_latency_seconds"),
            "Database query latency in seconds",
            ["operation", "collection"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=self.registry,
        )

        # Database operations counter
        self.db_operations_total = Counter(
            self._metric_name("db_operations_total"),
            "Total number of database operations",
            ["operation", "collection", "status"],
            registry=self.registry,
        )

    def _init_auth_metrics(self) -> None:
        """Initialize authentication metrics."""
        # Auth attempts counter
        self.auth_attempts_total = Counter(
            self._metric_name("auth_attempts_total"),
            "Total number of authentication attempts",
            ["method", "status"],
            registry=self.registry,
        )

        # Active sessions gauge
        self.active_sessions = Gauge(
            self._metric_name("active_sessions"),
            "Number of active user sessions",
            registry=self.registry,
        )

        # Token operations counter
        self.token_operations_total = Counter(
            self._metric_name("token_operations_total"),
            "Total number of token operations",
            ["operation", "status"],
            registry=self.registry,
        )

    def _init_business_metrics(self) -> None:
        """Initialize business-specific metrics."""
        # Chat queries counter
        self.chat_queries_total = Counter(
            self._metric_name("chat_queries_total"),
            "Total number of chat queries",
            ["status"],
            registry=self.registry,
        )

        # Query length histogram
        self.query_length = Histogram(
            self._metric_name("query_length_chars"),
            "Chat query length in characters",
            buckets=[10, 50, 100, 200, 500, 1000, 2000],
            registry=self.registry,
        )

        # Response length histogram
        self.response_length = Histogram(
            self._metric_name("response_length_chars"),
            "Chat response length in characters",
            buckets=[50, 100, 200, 500, 1000, 2000, 5000],
            registry=self.registry,
        )

        # Document retrieval metrics
        self.documents_retrieved = Histogram(
            self._metric_name("documents_retrieved_count"),
            "Number of documents retrieved per query",
            buckets=[0, 1, 2, 3, 4, 5, 10],
            registry=self.registry,
        )

    def _init_system_metrics(self) -> None:
        """Initialize system metrics."""
        # Rate limit hits counter
        self.rate_limit_hits_total = Counter(
            self._metric_name("rate_limit_hits_total"),
            "Total number of rate limit hits",
            ["endpoint"],
            registry=self.registry,
        )

        # Cache metrics
        self.cache_hits_total = Counter(
            self._metric_name("cache_hits_total"),
            "Total number of cache hits",
            ["cache_type"],
            registry=self.registry,
        )

        self.cache_misses_total = Counter(
            self._metric_name("cache_misses_total"),
            "Total number of cache misses",
            ["cache_type"],
            registry=self.registry,
        )

        # Health check status gauge
        self.health_check_status = Gauge(
            self._metric_name("health_check_status"),
            "Health check status (1=healthy, 0=unhealthy)",
            ["component"],
            registry=self.registry,
        )

    def track_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        latency: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
    ) -> None:
        """
        Track an HTTP request.

        Args:
            method: HTTP method
            endpoint: Request endpoint
            status_code: Response status code
            latency: Request latency in seconds
            request_size: Request body size in bytes
            response_size: Response body size in bytes
        """
        self.requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()

        self.request_latency.labels(
            method=method,
            endpoint=endpoint
        ).observe(latency)

        if request_size is not None:
            self.request_size.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)

        if response_size is not None:
            self.response_size.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)

    def track_llm_inference(
        self,
        model: str,
        operation: str,
        latency: float,
        success: bool,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> None:
        """
        Track an LLM inference operation.

        Args:
            model: Model name
            operation: Operation type (inference, embedding, etc.)
            latency: Inference latency in seconds
            success: Whether operation succeeded
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.llm_inference_latency.labels(
            model=model,
            operation=operation
        ).observe(latency)

        status = "success" if success else "failure"
        self.llm_requests_total.labels(
            model=model,
            status=status
        ).inc()

        if input_tokens is not None:
            self.llm_tokens_total.labels(
                model=model,
                token_type="input"
            ).inc(input_tokens)

        if output_tokens is not None:
            self.llm_tokens_total.labels(
                model=model,
                token_type="output"
            ).inc(output_tokens)

    def track_chat_query(
        self,
        query_length: int,
        response_length: int,
        success: bool,
    ) -> None:
        """
        Track a chat query.

        Args:
            query_length: Query length in characters
            response_length: Response length in characters
            success: Whether query succeeded
        """
        status = "success" if success else "failure"
        self.chat_queries_total.labels(status=status).inc()
        self.query_length.observe(query_length)
        self.response_length.observe(response_length)

    def get_metrics(self) -> bytes:
        """Generate metrics output for Prometheus scraping."""
        return generate_latest(self.registry)

    def get_content_type(self) -> str:
        """Get the content type for metrics endpoint."""
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
metrics = MetricsCollector()
