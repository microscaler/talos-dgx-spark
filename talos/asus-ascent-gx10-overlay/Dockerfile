# Multi-stage Dockerfile for Talos overlay image
# Stage 1: Build installer binary
FROM --platform=linux/arm64 golang:1.22.7-alpine AS builder
WORKDIR /build
COPY installer/ ./installer/
WORKDIR /build/installer
RUN go mod tidy && \
    GOOS=linux GOARCH=arm64 go build -o /build/installer/asus-ascent-gx10-overlay ./installer.go && \
    chmod +x /build/installer/asus-ascent-gx10-overlay

# Stage 2: Create overlay image
FROM scratch
# Copy overlay files (excluding installer source)
COPY install/ /overlay/install/
COPY files/ /overlay/files/
COPY overlay.yaml /overlay/overlay.yaml
# Copy built installer binary
COPY --from=builder /build/installer/asus-ascent-gx10-overlay /overlay/installers/asus-ascent-gx10-overlay

