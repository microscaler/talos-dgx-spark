# Multi-stage Dockerfile for Talos overlay image
# Build arguments for platform
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Stage 1: Build installer binary
FROM golang:1.22.7-alpine AS builder
ARG TARGETPLATFORM
ARG BUILDPLATFORM
WORKDIR /build
COPY installer/ ./installer/
WORKDIR /build/installer
# Extract GOOS and GOARCH from TARGETPLATFORM (e.g., linux/arm64 -> GOOS=linux GOARCH=arm64)
RUN GOOS=$(echo ${TARGETPLATFORM} | cut -d'/' -f1) && \
    GOARCH=$(echo ${TARGETPLATFORM} | cut -d'/' -f2) && \
    go mod tidy && \
    GOOS=${GOOS} GOARCH=${GOARCH} go build -o /build/installer/asus-ascent-gx10-overlay ./installer.go && \
    chmod +x /build/installer/asus-ascent-gx10-overlay

# Stage 2: Create overlay image
FROM scratch
# Copy all overlay files at ROOT level (not under /overlay/)
# The imager extracts to tempDir/overlay/, so files at root become tempDir/overlay/...
# This ensures the imager can find all files when extracting the overlay
COPY install/ /install/
COPY files/ /files/
COPY overlay.yaml /overlay.yaml
# Copy installer binary last - this ensures it's in the final layer
# The installer must be at /installers/{overlay-name} in the image
# When extracted to tempDir/overlay/, it becomes tempDir/overlay/installers/{overlay-name}
# Use --chmod=755 to explicitly ensure executable permissions are set
COPY --from=builder --chmod=755 /build/installer/asus-ascent-gx10-overlay /installers/asus-ascent-gx10-overlay

