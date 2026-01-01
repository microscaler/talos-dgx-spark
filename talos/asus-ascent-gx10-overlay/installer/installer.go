// Package main implements the Talos overlay installer for ASUS Ascent GX10
//
// This installer adds NVIDIA GPU support to Talos Linux by:
// - Installing NVIDIA kernel modules
// - Installing GPU firmware
// - Configuring boot parameters
// - Setting up module loading
//
// The installer is called by Talos imager with "install" as the first argument
// and YAML InstallOptions passed via stdin.
package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"

	"go.yaml.in/yaml/v4"
)

// InstallOptions matches the structure from Talos overlay package
type InstallOptions struct {
	InstallDisk   string                 `yaml:"installDisk"`
	MountPrefix   string                 `yaml:"mountPrefix"`
	ArtifactsPath string                 `yaml:"artifactsPath"`
	ExtraOptions  map[string]interface{} `yaml:"extraOptions,omitempty"`
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <command>\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "Commands: install\n")
		os.Exit(1)
	}

	command := os.Args[1]

	switch command {
	case "install":
		if err := install(); err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}
	case "get-options":
		// Return empty options for now (can be extended later)
		options := map[string]interface{}{
			"name":       "asus-ascent-gx10-overlay",
			"kernelArgs": []string{},
		}
		if err := yaml.NewEncoder(os.Stdout).Encode(options); err != nil {
			fmt.Fprintf(os.Stderr, "Error encoding options: %v\n", err)
			os.Exit(1)
		}
	default:
		fmt.Fprintf(os.Stderr, "Unknown command: %s\n", command)
		os.Exit(1)
	}
}

func install() error {
	// Read YAML InstallOptions from stdin
	var options InstallOptions
	if err := yaml.NewDecoder(os.Stdin).Decode(&options); err != nil {
		return fmt.Errorf("failed to decode install options: %w", err)
	}

	// MountPrefix is the rootfs path
	rootfsPath := options.MountPrefix

	// Overlay path is the directory containing the installer's parent directory
	// The installer is at: /tmp/imager.../overlay/installers/asus-ascent-gx10-overlay
	// So overlay is at: /tmp/imager.../overlay/
	executablePath, err := os.Executable()
	if err != nil {
		// Fallback: try to get from /proc/self/exe or use a default
		executablePath = os.Args[0]
	}
	// Get the directory containing installers/ (which is the overlay directory)
	installersDir := filepath.Dir(executablePath)
	overlayPath := filepath.Dir(installersDir)

	fmt.Printf("Installing ASUS Ascent GX10 overlay...\n")
	fmt.Printf("  Overlay path: %s\n", overlayPath)
	fmt.Printf("  Rootfs path: %s\n", rootfsPath)

	// Install kernel modules
	if err := installKernelModules(overlayPath, rootfsPath); err != nil {
		return fmt.Errorf("failed to install kernel modules: %w", err)
	}

	// Install firmware
	if err := installFirmware(overlayPath, rootfsPath); err != nil {
		return fmt.Errorf("failed to install firmware: %w", err)
	}

	// Install configuration files
	if err := installConfigFiles(overlayPath, rootfsPath); err != nil {
		return fmt.Errorf("failed to install config files: %w", err)
	}

	fmt.Printf("✅ Overlay installation completed successfully\n")
	return nil
}

// installKernelModules installs NVIDIA kernel modules
func installKernelModules(overlayPath, rootfsPath string) error {
	// Check both artifacts/install/ and install/ for backward compatibility
	sourceDir := filepath.Join(overlayPath, "artifacts", "install", "kernel-modules")
	if _, err := os.Stat(sourceDir); os.IsNotExist(err) {
		// Fallback to direct install/ path
		sourceDir = filepath.Join(overlayPath, "install", "kernel-modules")
	}
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
	// Check both artifacts/install/ and install/ for backward compatibility
	sourceDir := filepath.Join(overlayPath, "artifacts", "install", "firmware")
	if _, err := os.Stat(sourceDir); os.IsNotExist(err) {
		// Fallback to direct install/ path
		sourceDir = filepath.Join(overlayPath, "install", "firmware")
	}
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
	// Check both artifacts/files/ and files/ for backward compatibility
	filesDir := filepath.Join(overlayPath, "artifacts", "files")
	if _, err := os.Stat(filesDir); os.IsNotExist(err) {
		// Fallback to direct files/ path
		filesDir = filepath.Join(overlayPath, "files")
	}

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

