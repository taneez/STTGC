import torch
from torch import nn


class Swish(nn.Module):
    def __init__(self, inplace=False):
        super(Swish, self).__init__()
        self.inplace = inplace

    def forward(self, x):
        return x.mul_(x.sigmoid()) if self.inplace else x.mul(x.sigmoid())


class HardSwish(nn.Module):
    def __init__(self, inplace=False):
        super(HardSwish, self).__init__()
        self.inplace = inplace

    def forward(self, x):
        inner = nn.functional.relu6(x + 3.).div_(6.)
        return x.mul_(inner) if self.inplace else x.mul(inner)


class AconC(nn.Module):
    r""" ACON activation (activate or not).
    # AconC: (p1*x-p2*x) * sigmoid(beta*(p1*x-p2*x)) + p2*x, beta is a learnable parameter
    # according to "Activate or Not: Learning Customized Activation" <https://arxiv.org/pdf/2009.04759.pdf>.
    """
    def __init__(self, channel):
        super(AconC).__init__()
        self.p1 = nn.Parameter(torch.randn(1, channel, 1, 1))
        self.p2 = nn.Parameter(torch.randn(1, channel, 1, 1))
        self.beta = nn.Parameter(torch.ones(1, channel, 1, 1))

    def forward(self, x):
        return (self.p1 * x - self.p2 * x) * (self.beta * (self.p1 * x - self.p2 * x)).sigmoid() + self.p2 * x


class MetaAconC(nn.Module):
    r""" ACON activation (activate or not).
    # MetaAconC: (p1*x-p2*x) * sigmoid(beta*(p1*x-p2*x)) + p2*x, beta is generated by a small network
    # according to "Activate or Not: Learning Customized Activation" <https://arxiv.org/pdf/2009.04759.pdf>.
    """
    def __init__(self, channel, r=4):
        super().__init__()
        inner_channel = max(r, channel // r)
        self.fcn = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(channel, inner_channel, 1),
            nn.BatchNorm2d(inner_channel),
            nn.Conv2d(inner_channel, channel, 1),
            nn.BatchNorm2d(channel),
            nn.Sigmoid(),
        )
        self.p1 = nn.Parameter(torch.randn(1, channel, 1, 1))
        self.p2 = nn.Parameter(torch.randn(1, channel, 1, 1))

    def forward(self, x, **kwargs):
        return (self.p1 * x - self.p2 * x) * (self.fcn(x) * (self.p1 * x - self.p2 * x)).sigmoid() + self.p2 * x


class Activations(nn.Module):
    def __init__(self, act):
        super(Activations, self).__init__()
        if act == 'relu':
            self.act = nn.ReLU(inplace=True)
        elif act == 'swish':
            self.act = Swish(inplace=True)
        elif act == 'hswish':
            self.act = HardSwish(inplace=True)
        else:
            self.act = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.act(x)


