import torch


def _safe_amax_scale(x, qmax):
    flat = x.detach().to(torch.float32).reshape(-1, x.shape[-1])
    scale = flat.abs().amax(dim=-1, keepdim=True).clamp(min=1.0e-6) / qmax
    return scale.reshape(*x.shape[:-1], 1)


def scaled_int8_quant(x, scale=None, azp=None, symmetric=True):
    if scale is None:
        scale = _safe_amax_scale(x, 127.0)
    q = torch.round(x.to(torch.float32) / scale).clamp(-127, 127).to(torch.int8)
    return q, scale.to(torch.float32), None


def scaled_fp8_quant(x, scale=None, scale_ub=None, use_per_token_if_dynamic=True):
    if scale is None:
        scale = _safe_amax_scale(x, 448.0)
    q = (x.to(torch.float32) / scale).clamp(-448, 448).to(torch.float8_e4m3fn)
    return q, scale.to(torch.float32)
