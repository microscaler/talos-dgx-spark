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
# Copy all overlay files in a single layer to ensure they're all together
# This ensures the imager can find all files when extracting the overlay
# The installer must be at /overlay/installers/{overlay-name} for the imager to find it
# We copy everything in one layer to avoid layer extraction issues
COPY --from=builder /build/installer/asus-ascent-gx10-overlay /overlay/installers/asus-ascent-gx10-overlay
COPY install/ /overlay/install/
COPY files/ /overlay/files/
COPY overlay.yaml /overlay/overlay.yaml

