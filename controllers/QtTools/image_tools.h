#ifndef IMAGE_TOOLS_H
#define IMAGE_TOOLS_H

#include <QImage>
#include <QColor>
#include <QPainter>
#include <QPen>
#include <QPainterPath>
#include <QGraphicsScene>
#include <unordered_map>
#include <vector>
#include <queue>

void floodFill(QImage &layer, int x, int y, const QColor &color);
void eraseArea(QImage &layer, int x, int y, int a = 5, int b = 5);
void drawIcon(QImage &layer, const QImage &icon, int x, int y);
QImage recolorIcon(QImage image, const QColor &targetColor);

class PixelSampler {
public:
    PixelSampler(const QImage &image, const std::vector<QPoint> &samplePositions,
                 const std::unordered_map<std::string, QColor> &states, int tolerance = 5);

    std::unordered_map<std::string, int> samplePixels() const;

private:
    QImage image;
    std::vector<QPoint> samplePositions;
    std::unordered_map<std::string, QColor> states;
    int tolerance;

    bool isSimilarColor(const QColor &color1, const QColor &color2, int tolerance) const;
};

class IconFinder {
public:
    IconFinder(const QImage &sampleIcon, const QImage &layer);
    std::vector<QPoint> findIconPositions();

private:
    QImage sampleIcon;
    QImage layer;
    int iconWidth, iconHeight;
    int layerWidth, layerHeight;
};

class DrawPath {
public:
    DrawPath(QImage &layer, QGraphicsScene &scene, QColor color = QColor(128, 128, 128, 255),
             int width = 2, int zValue = 10);
    void drawPath(int x, int y, bool isStart);

private:
    int zValue;
    QImage &layer;
    QColor color;
    int width;
    QGraphicsScene &scene;
    QPainterPath path;
    QGraphicsPathItem *previewItem;
};

#endif
