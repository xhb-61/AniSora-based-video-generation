import torch


def _as_2d_scale(scale, rows, device):
    if scale is None:
        return None
    scale = scale.to(device=device, dtype=torch.float32)
    if scale.ndim == 0:
        return scale.reshape(1, 1).expand(rows, 1)
    return scale.reshape(rows, -1)[:, :1]


def _dequantize(x, scale, out_dtype):
    if out_dtype is None:
        out_dtype = torch.bfloat16
    x_float = x.to(torch.float32)
    scale = _as_2d_scale(scale, x_float.shape[0], x_float.device)
    if scale is not None:
        x_float = x_float * scale
    return x_float.to(out_dtype)


def _linear(a, b, bias=None, scale_a=None, scale_b=None, out_dtype=None):
    out_dtype = out_dtype or torch.bfloat16
    a_deq = _dequantize(a, scale_a, out_dtype)
    b_deq = _dequantize(b, scale_b, out_dtype)
    out = a_deq.matmul(b_deq.transpose(-1, -2))
    if bias is not None:
        out = out + bias.to(device=out.device, dtype=out.dtype)
    return out


def q8_linear(a, b, bias=None, scale_a=None, scale_b=None, fuse_gelu=False, out_dtype=None):
    out = _linear(a, b, bias=bias, scale_a=scale_a, scale_b=scale_b, out_dtype=out_dtype)
    if fuse_gelu:
        out = torch.nn.functional.gelu(out)
    return out


def fp8_linear(a, b, bias=None, scale_a=None, scale_b=None, use_hadamard=False, out_dtype=None):
    return _linear(a, b, bias=bias, scale_a=scale_a, scale_b=scale_b, out_dtype=out_dtype)
