import torch
import torch.nn as nn

class VGG16_FCN(nn.Module):
    def __init__(self, num_classes=21):
        super(VGG16_FCN, self).__init__()

        self.features1 = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/2 크기
        )
        
        self.features2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/4 크기
        )
        
        self.features3 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/8 크기
        )

        self.features4 = nn.Sequential(
            nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/16 크기
        )

        self.features5 = nn.Sequential(
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/32 크기
        )

        # Fully connected layers (converted to convolutions)
        self.conv6 = nn.Conv2d(512, 4096, kernel_size=3, padding=1)
        self.conv7 = nn.Conv2d(4096, 4096, kernel_size=1)
        self.score = nn.Conv2d(4096, num_classes, kernel_size=1)

        # 추가: score를 7x7에서 14x14로 업샘플링
        self.score_upsample = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=4, stride=2, padding=1)
        self.score_upsample2 = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=4, stride=2, padding=1)
        
        # Score layers for FCN-16s, FCN-8s
        self.score4 = nn.Conv2d(512, num_classes, kernel_size=1)  # 1/16 크기
        self.score3 = nn.Conv2d(256, num_classes, kernel_size=1)  # 1/8 크기

        # Transposed Convolution
        self.upscore32 = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=64, stride=32, padding=16, bias=False)
        self.deconv16 = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=32, stride=16, padding=8, bias=False)
        self.deconv8 = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=16, stride=8, padding=4, bias=False)     # 1/16 -> 1/8 크기

    def forward(self, x):
        # Features extraction through VGG16
        x1 = self.features1(x)
        x2 = self.features2(x1)
        x3 = self.features3(x2)
        x4 = self.features4(x3)
        x5 = self.features5(x4)

        # Fully connected layers
        x6 = self.conv6(x5)
        x7 = self.conv7(x6)
        score = self.score(x7)

        # FCN-32s
        fcn32 = self.upscore32(score)
        
        # FCN-16s
        score2 = self.score_upsample(score)
        fcn16 = self.deconv16(score2)
        score4 = self.score4(x4) 

        score4_1 = score4 + score2
        
        # FCN-8s
        score3 = self.score3(x3)
        score4_2 = self.score_upsample2(score4_1)
        score3_1 = score3 + score4_2
        fcn8 = self.deconv8(score3_1)

        return fcn32, fcn16, fcn8

if __name__ == "__main__":
    model = VGG16_FCN(num_classes=21)
    input = torch.ones([1, 3, 224, 224])
    fcn32, fcn16, fcn8 = model(input)
    print(f"Final shapes - FCN32: {fcn32.shape}, FCN16: {fcn16.shape}, FCN8: {fcn8.shape}")