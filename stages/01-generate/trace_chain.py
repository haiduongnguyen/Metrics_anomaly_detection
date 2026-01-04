import uuid
import json

def generate_trace_chain(topology):
    """
    Trả về danh sách span theo đúng topology.
    Mỗi span có: trace_id, span_id, parent_span_id, service
    """
    trace_id = uuid.uuid4().hex
    spans = []

    def walk(service, parent_span_id=None):
        span_id = uuid.uuid4().hex[:16]
        spans.append({
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "service": service
        })
        for child in topology.get(service, []):
            walk(child, span_id)

    # Root = payment-service (có thể thay đổi theo config)
    walk("payment-service")
    return spans
