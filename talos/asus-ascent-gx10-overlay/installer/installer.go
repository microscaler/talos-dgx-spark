// Package installer implements the Talos overlay installer for ASUS Ascent GX10
//
// This installer adds NVIDIA GPU support to Talos Linux by:
// - Installing NVIDIA kernel modules
// - Installing GPU firmware
// - Configuring boot parameters
// - Setting up module loading
package installer

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"github.com/siderolabs/talos/pkg/imager/overlay"
)

// Installer implements the overlay.Installer interface
type Installer struct {
	overlayPath string
}

// NewInstaller creates a new ASUS Ascent GX10 overlay installer
func NewInstaller(overlayPath string) *Installer {
	return &Installer{
		overlayPath: overlayPath,
	}
}

// Install implements the overlay.Installer interface
func (i *Installer) Install(ctx context.Context, options *overlay.InstallerOptions) error {
	// Install kernel modules
	if err := i.installKernelModules(ctx, options); err != nil {
		return fmt.Errorf("failed to install kernel modules: %w", err)
	}

	// Install firmware
	if err := i.installFirmware(ctx, options); err != nil {
		return fmt.Errorf("failed to install firmware: %w", err)
	}

	// Install configuration files
	if err := i.installConfigFiles(ctx, options); err != nil {
		return fmt.Errorf("failed to install config files: %w", err)
	}

	// Configure boot parameters
	if err := i.configureBootParams(ctx, options); err != nil {
		return fmt.Errorf("failed to configure boot params: %w", err)
	}

	return nil
}

// installKernelModules installs NVIDIA kernel modules
func (i *Installer) installKernelModules(ctx context.Context, options *overlay.InstallerOptions) error {
	sourceDir := filepath.Join(i.overlayPath, "install", "kernel-modules")
	targetDir := filepath.Join(options.RootfsPath, "lib", "modules")

	if _, err := os.Stat(sourceDir); os.IsNotExist(err) {
		return fmt.Errorf("kernel modules directory not found: %s", sourceDir)
	}

	// Copy kernel modules to target
	// TODO: Implement module copying logic
	// This should preserve module structure and dependencies

	return nil
}

// installFirmware installs GPU firmware blobs
func (i *Installer) installFirmware(ctx context.Context, options *overlay.InstallerOptions) error {
	sourceDir := filepath.Join(i.overlayPath, "install", "firmware")
	targetDir := filepath.Join(options.RootfsPath, "lib", "firmware")

	if _, err := os.Stat(sourceDir); os.IsNotExist(err) {
		return fmt.Errorf("firmware directory not found: %s", sourceDir)
	}

	// Copy firmware to target
	// TODO: Implement firmware copying logic
	// This should preserve firmware directory structure

	return nil
}

// installConfigFiles installs configuration files
func (i *Installer) installConfigFiles(ctx context.Context, options *overlay.InstallerOptions) error {
	filesDir := filepath.Join(i.overlayPath, "files")

	if _, err := os.Stat(filesDir); os.IsNotExist(err) {
		// No config files to install
		return nil
	}

	// Copy configuration files to target
	// TODO: Implement file copying logic
	// This should preserve file permissions and directory structure

	return nil
}

// configureBootParams configures kernel boot parameters
func (i *Installer) configureBootParams(ctx context.Context, options *overlay.InstallerOptions) error {
	// Add NVIDIA boot parameters to kernel command line
	// TODO: Implement boot parameter configuration
	// This should append NVIDIA-specific parameters to the kernel cmdline

	return nil
}

