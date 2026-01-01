// Package main implements the Talos overlay installer for ASUS Ascent GX10
//
// This installer adds NVIDIA GPU support to Talos Linux by:
// - Installing NVIDIA kernel modules
// - Installing GPU firmware
// - Configuring boot parameters
// - Setting up module loading
//
// The installer is called by Talos imager with the overlay path as the first argument
// and the rootfs path as the second argument.
package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
)

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintf(os.Stderr, "Usage: %s <overlay-path> <rootfs-path>\n", os.Args[0])
		os.Exit(1)
	}

	overlayPath := os.Args[1]
	rootfsPath := os.Args[2]

	fmt.Printf("Installing ASUS Ascent GX10 overlay...\n")
	fmt.Printf("  Overlay path: %s\n", overlayPath)
	fmt.Printf("  Rootfs path: %s\n", rootfsPath)

	// Install kernel modules
	if err := installKernelModules(overlayPath, rootfsPath); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to install kernel modules: %v\n", err)
		os.Exit(1)
	}

	// Install firmware
	if err := installFirmware(overlayPath, rootfsPath); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to install firmware: %v\n", err)
		os.Exit(1)
	}

	// Install configuration files
	if err := installConfigFiles(overlayPath, rootfsPath); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to install config files: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("✅ Overlay installation completed successfully\n")
}

// installKernelModules installs NVIDIA kernel modules
func installKernelModules(overlayPath, rootfsPath string) error {
	sourceDir := filepath.Join(overlayPath, "install", "kernel-modules")
	targetDir := filepath.Join(rootfsPath, "lib", "modules")

	if _, err := os.Stat(sourceDir); os.IsNotExist(err) {
		fmt.Printf("⚠️  Kernel modules directory not found: %s (skipping)\n", sourceDir)
		return nil
	}

	fmt.Printf("📦 Installing kernel modules from %s to %s\n", sourceDir, targetDir)
	return copyDirectory(sourceDir, targetDir)
}

// installFirmware installs GPU firmware blobs
func installFirmware(overlayPath, rootfsPath string) error {
	sourceDir := filepath.Join(overlayPath, "install", "firmware")
	targetDir := filepath.Join(rootfsPath, "lib", "firmware")

	if _, err := os.Stat(sourceDir); os.IsNotExist(err) {
		fmt.Printf("⚠️  Firmware directory not found: %s (skipping)\n", sourceDir)
		return nil
	}

	fmt.Printf("📦 Installing firmware from %s to %s\n", sourceDir, targetDir)
	return copyDirectory(sourceDir, targetDir)
}

// installConfigFiles installs configuration files
func installConfigFiles(overlayPath, rootfsPath string) error {
	filesDir := filepath.Join(overlayPath, "files")

	if _, err := os.Stat(filesDir); os.IsNotExist(err) {
		fmt.Printf("⚠️  Config files directory not found: %s (skipping)\n", filesDir)
		return nil
	}

	fmt.Printf("📦 Installing config files from %s to %s\n", filesDir, rootfsPath)
	return copyDirectory(filesDir, rootfsPath)
}

// copyDirectory recursively copies a directory
func copyDirectory(src, dst string) error {
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		relPath, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}

		dstPath := filepath.Join(dst, relPath)

		if info.IsDir() {
			return os.MkdirAll(dstPath, info.Mode())
		}

		// Create parent directory if it doesn't exist
		if err := os.MkdirAll(filepath.Dir(dstPath), 0755); err != nil {
			return err
		}

		// Copy file
		return copyFile(path, dstPath, info.Mode())
	})
}

// copyFile copies a file from src to dst
func copyFile(src, dst string, mode os.FileMode) error {
	srcFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer srcFile.Close()

	dstFile, err := os.OpenFile(dst, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, mode)
	if err != nil {
		return err
	}
	defer dstFile.Close()

	_, err = io.Copy(dstFile, srcFile)
	return err
}

