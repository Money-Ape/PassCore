using System.Runtime.InteropServices;

namespace PassCore.Utilities.Core;

public static class PassCorePaths{
    public static string PassCoreDirectory{
        get{
            if (OperatingSystem.IsLinux()){
                return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".local", "share", "passcore");
            }
            if (OperatingSystem.IsWindows()){
                string appData = Environment.GetEnvironmentVariable("APPDATA") ?? throw new InvalidOperationException("APPDATA environment variable is not available.!");
                return Path.Combine(appData, "PassCore");
            }
            throw new PlatformNotSupportedException($"Unsupported operating system: {RuntimeInformation.OSDescription}");
        }
    }
    
    public static string ContainerDirectory{
        get{
            if (OperatingSystem.IsLinux()){
                return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".local", "share", ".passcore_db");
            }
            if (OperatingSystem.IsWindows()){
                string localappData = Environment.GetEnvironmentVariable("LOCALAPPDATA") ?? throw new InvalidOperationException("LOCALAPPDATA environment variable is not available.!");
                return Path.Combine(localappData, "PassCoreData");
            }
            throw new PlatformNotSupportedException($"Unsupported operating system: {RuntimeInformation.OSDescription}");
        }
    }

    public static string NotesContainerDirectory => Path.Combine(ContainerDirectory, "notes");
    public static string ImageContainerDirectory => Path.Combine(ContainerDirectory, "images");
    public static string SaltFile => Path.Combine(PassCoreDirectory, "vault.salt");
    public static string NotesMetaData => Path.Combine(PassCoreDirectory, "notes_index.json");
    public static string ImagesMetaData => Path.Combine(PassCoreDirectory, "images_index.json");
    public static string SettingsFile => Path.Combine(PassCoreDirectory, "settings.yaml");
    public static string BackupDirectory => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Documents", "PassCore Backups");

    public static void EnsureDirectories(){
        Directory.CreateDirectory(PassCoreDirectory);
        Directory.CreateDirectory(ContainerDirectory);
        Directory.CreateDirectory(BackupDirectory);
    }
}