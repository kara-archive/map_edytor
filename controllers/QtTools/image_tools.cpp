#include "image_tools.h"

void floodFill(QImage &layer, int x, int y, const QColor &color) {
    int height = layer.height(), width = layer.width();
    QColor startColor = QColor(layer.pixel(x, y));
    if (startColor == color) return;

    std::queue<QPoint> queue;
    std::unordered_set<int> visited;
    queue.push(QPoint(x, y));

    while (!queue.empty()) {
        QPoint p = queue.front();
        queue.pop();

        if (p.x() < 0 || p.y() < 0 || p.x() >= width || p.y() >= height) continue;
        if (QColor(layer.pixel(p.x(), p.y())) != startColor) continue;

        layer.setPixel(p.x(), p.y(), color.rgb());

        queue.push(QPoint(p.x() + 1, p.y()));
        queue.push(QPoint(p.x() - 1, p.y()));
        queue.push(QPoint(p.x(), p.y() + 1));
        queue.push(QPoint(p.x(), p.y() - 1));
    }
}

void eraseArea(QImage &layer, int x, int y, int a, int b) {
    QPainter painter(&layer);
    painter.setCompositionMode(QPainter::CompositionMode_Clear);
    painter.setBrush(Qt::transparent);
    painter.drawRect(x - a, y - b, a * 2, b * 2);
}

void drawIcon(QImage &layer, const QImage &icon, int x, int y) {
    QPainter painter(&layer);
    painter.drawImage(x - icon.width() / 2, y - icon.height() / 2, icon);
}

QImage recolorIcon(QImage image, const QColor &targetColor) {
    image = image.convertToFormat(QImage::Format_ARGB32);
    for (int y = 0; y < image.height(); ++y) {
        for (int x = 0; x < image.width(); ++x) {
            if (QColor(image.pixel(x, y)) == QColor(255, 255, 255)) {
                image.setPixel(x, y, targetColor.rgb());
            }
        }
    }
    return image;
}

PixelSampler::PixelSampler(const QImage &image, const std::vector<QPoint> &samplePositions,
                           const std::unordered_map<std::string, QColor> &states, int tolerance)
    : image(image), samplePositions(samplePositions), states(states), tolerance(tolerance) {}

std::unordered_map<std::string, int> PixelSampler::samplePixels() const {
    std::unordered_map<std::string, int> counts;
    for (const auto &[name, color] : states) {
        counts[name] = 0;
    }

    for (const QPoint &pos : samplePositions) {
        QColor color = QColor(image.pixel(pos.x(), pos.y()));
        for (const auto &[name, stateColor] : states) {
            if (isSimilarColor(color, stateColor, tolerance)) {
                counts[name]++;
                break;
            }
        }
    }
    return counts;
}

bool PixelSampler::isSimilarColor(const QColor &color1, const QColor &color2, int tolerance) const {
    return std::abs(color1.red() - color2.red()) <= tolerance &&
           std::abs(color1.green() - color2.green()) <= tolerance &&
           std::abs(color1.blue() - color2.blue()) <= tolerance;
}

IconFinder::IconFinder(const QImage &sampleIcon, const QImage &layer)
    : sampleIcon(sampleIcon), layer(layer) {}

std::vector<QPoint> IconFinder::findIconPositions() {
    std::vector<QPoint> positions;
    // Algorytm wyszukiwania ikon na obrazie
    return positions;
}

DrawPath::DrawPath(QImage &layer, QGraphicsScene &scene, QColor color, int width, int zValue)
    : layer(layer), scene(scene), color(color), width(width), zValue(zValue), previewItem(nullptr) {}

void DrawPath::drawPath(int x, int y, bool isStart) {
    if (isStart) {
        path.moveTo(x, y);
    } else {
        path.lineTo(x, y);
    }

    QPainter painter(&layer);
    QPen pen(color);
    pen.setWidth(width);
    painter.setPen(pen);
    painter.drawPath(path);
}
