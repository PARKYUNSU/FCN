import torch
import torch.nn as nn

class VGG16_FCN(nn.Module):
    def __init__(self, num_classes=21):
        super(VGG16_FCN, self).__init__()
        
        self.num_classes = num_classes

        self.features1 = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # [1, 64, 112, 112]
        )
        
        self.features2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # [1, 128, 56, 56]
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
            nn.MaxPool2d(kernel_size=2, stride=2),  # [1, 256, 28, 28]
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
            nn.MaxPool2d(kernel_size=2, stride=2),  # [1, 512, 14, 14]
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
            nn.MaxPool2d(kernel_size=2, stride=2),  # [1, 512, 7, 7]
        )

        # Fully connected layers
        self.conv6 = nn.Sequential(
            nn.Conv2d(512, 4096, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Dropout2d(p=0.5)  # [1, 4096, 7, 7]
        )
        self.conv7 = nn.Sequential(
            nn.Conv2d(4096, 4096, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Dropout2d(p=0.5)  # [1, 4096, 7, 7]
        )
        self.score = nn.Conv2d(4096, num_classes, kernel_size=1)  # [1, 21, 7, 7]

        # score 7x7 -> 14x14 업샘플링,
        self.score_upsample = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=4, stride=2, padding=1)  # [1, 21, 14, 14]
        # 14x14 -> 28x28
        self.score_upsample2 = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=4, stride=2, padding=1)  # [1, 21, 28, 28]
        
        # Score layers for FCN-16s, FCN-8s
        self.score4 = nn.Conv2d(512, num_classes, kernel_size=1)  # [1, 21, 14, 14] 
        self.score3 = nn.Conv2d(256, num_classes, kernel_size=1)  # [1, 21, 28, 28]

        # Transposed Convolution
        self.upscore32 = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=64, stride=32, padding=16, bias=False)  # [1, 21, 224, 224]
        self.deconv16 = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=32, stride=16, padding=8, bias=False)  # [1, 21, 224, 224]
        self.deconv8 = nn.ConvTranspose2d(num_classes, num_classes, kernel_size=16, stride=8, padding=4, bias=False)  # [1, 21, 224, 224]

    def forward(self, x):
        # Features extraction through VGG16
        x1 = self.features1(x)  # [1, 64, 112, 112]
        x2 = self.features2(x1)  # [1, 128, 56, 56]
        x3 = self.features3(x2)  # [1, 256, 28, 28]
        x4 = self.features4(x3)  # [1, 512, 14, 14]
        x5 = self.features5(x4)  # [1, 512, 7, 7]

        # Fully connected layers
        x6 = self.conv6(x5)  # [1, 4096, 7, 7]
        x7 = self.conv7(x6)  # [1, 4096, 7, 7]
        score = self.score(x7)  # [1, 21, 7, 7]

        # FCN-32s
        fcn32 = self.upscore32(score)  # [1, 21, 224, 224]

        # FCN-16s
        score2 = self.score_upsample(score)  # [1, 21, 14, 14]
        score4 = self.score4(x4)  # [1, 21, 14, 14] 
        score4_1 = score4 + score2  # [1, 21, 14, 14]
        fcn16 = self.deconv16(score4_1)  # [1, 21, 224, 224]

        # FCN-8s
        score3 = self.score3(x3)  # [1, 21, 28, 28]
        score4_2 = self.score_upsample2(score4_1)  # [1, 21, 28, 28]
        score3_1 = score3 + score4_2  # [1, 21, 28, 28]
        fcn8 = self.deconv8(score3_1)  # [1, 21, 224, 224]

        return fcn8


# 거중치 초기화 함수
def init_weights(m):
    if isinstance(m, nn.Conv2d):
        nn.init.xavier_uniform_(m.weight)
        if m.bias is not None:
            nn.init.constant_(m.bias, 0)
    elif isinstance(m, nn.Linear):
        nn.init.xavier_uniform_(m.weight)
        if m.bias is not None:
            nn.init.constant_(m.bias, 0)

# 모델 초기화 및 테스트
if __name__ == "__main__":
    model = VGG16_FCN(num_classes=21)
    model.apply(init_weights)  # Xavier 초기화 적용
    input = torch.ones([1, 3, 224, 224])
    fcn8 = model(input)