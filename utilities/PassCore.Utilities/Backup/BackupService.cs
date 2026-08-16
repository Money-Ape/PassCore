using System.IO.Compression;
using PassCore.Utilities.Core;
using PassCore.Utilities.Models;
using PassCore.Utilities.File;

namespace PassCore.Utilities.Backup;

public static class BackupService{
    private const int MaxBackups = 10;

    // DELETE DIRECTORY CONTENTS
    public static void DeleteDirectoryContents(string directory){
        if (!Directory.Exists(directory)){return;}

        foreach (string file in Directory.EnumerateFiles(directory, "*", System.IO.SearchOption.AllDirectories)){
            System.IO.File.Delete(file);
        }
        foreach (string dir in Directory.EnumerateDirectories(directory, "*", System.IO.SearchOption.AllDirectories).OrderByDescending(x => x.Length)){
            Directory.Delete(dir);
        }
    }

    // CREATE BACKUPS
    public static UtilityResponse Create(bool force){
        try{
           PassCorePaths.EnsureDirectories();
           string[] requiredFiles = {
                PassCorePaths.SaltFile,
                PassCorePaths.NotesMetaData,
                PassCorePaths.ImagesMetaData,
                PassCorePaths.SettingsFile
            };
            foreach (string file in requiredFiles){
                if (!System.IO.File.Exists(file)){
                    return UtilityResponse.Fail($"Required vault File is missing: {file}");
                }
            }
            string timestamp = DateTime.Now.ToString("ddMMyyyyHHmmss");
            string backupPath = Path.Combine(PassCorePaths.BackupDirectory, $"passcore_backup_{timestamp}.zip");

            using (FileStream stream = new FileStream(backupPath, FileMode.CreateNew, FileAccess.Write, FileShare.None)){
                using ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Create);

                AddFile.AddTo(archive, PassCorePaths.SaltFile, Path.GetFileName(PassCorePaths.SaltFile));
                AddFile.AddTo(archive, PassCorePaths.NotesMetaData, Path.GetFileName(PassCorePaths.NotesMetaData));
                AddFile.AddTo(archive, PassCorePaths.ImagesMetaData, Path.GetFileName(PassCorePaths.ImagesMetaData));
                AddFile.AddTo(archive, PassCorePaths.SettingsFile, Path.GetFileName(PassCorePaths.SettingsFile));

                if (Directory.Exists(PassCorePaths.ContainerDirectory)){
                    foreach(string file in Directory.EnumerateFiles(PassCorePaths.ContainerDirectory, "*", System.IO.SearchOption.AllDirectories)){
                        string relative = Path.GetRelativePath(PassCorePaths.ContainerDirectory, file);
                        AddFile.AddTo(archive, file, relative);
                    }
                }
            }
            RotateBackups();

            return UtilityResponse.Ok(new{
                path = backupPath,
                size = new FileInfo(backupPath).Length
            });
        }

        catch (Exception ex){
            return UtilityResponse.Fail($"Backup Failed: {ex.Message}");
        }
    }

    // RESTORE BACKUPS
    public static UtilityResponse Restore(string? backupPath){
        if (string.IsNullOrWhiteSpace(backupPath)){
            return UtilityResponse.Fail("Backup path was not provided.!");
        }
        if (!System.IO.File.Exists(backupPath)){
            return UtilityResponse.Fail("Backup file does not exist.!");
        }

        string stagingDirectory = Path.Combine(Path.GetTempPath(), $"passcore_backup_{Guid.NewGuid():N}");
        try{
           Directory.CreateDirectory(stagingDirectory);
           ZipFile.ExtractToDirectory(backupPath, stagingDirectory);
           string[] requiredFiles = {
                "vault.salt",
                "images_index.json",
                "notes_index.json",
                "settings.yaml"
            };
            foreach (string file in requiredFiles){
                if (!System.IO.File.Exists(Path.Combine(stagingDirectory, file))){
                    return UtilityResponse.Fail($"Backup is missing required file: {file}");
                }
            }

            // Do not destroy the existing vault until the archive has passed basic structural checks.
            DeleteDirectoryContents(PassCorePaths.ContainerDirectory);

            Directory.CreateDirectory(PassCorePaths.ContainerDirectory);
            MoveFile.Move(Path.Combine(stagingDirectory, "vault.salt"), PassCorePaths.SaltFile);
            MoveFile.Move(Path.Combine(stagingDirectory, "images_index.json"), PassCorePaths.ImagesMetaData);
            MoveFile.Move(Path.Combine(stagingDirectory, "notes_index.json"), PassCorePaths.NotesMetaData);
            MoveFile.Move(Path.Combine(stagingDirectory, "settings.yaml"), PassCorePaths.SettingsFile);

            foreach (string file in Directory.EnumerateFiles(stagingDirectory, "*", System.IO.SearchOption.AllDirectories)){
                string relative = Path.GetRelativePath(stagingDirectory, file);

                if (requiredFiles.Contains(relative, StringComparer.Ordinal)){continue;}

                string destination = Path.Combine(PassCorePaths.ContainerDirectory, relative);
                string? parent = Path.GetDirectoryName(destination);
                if (parent is not null){Directory.CreateDirectory(parent);}

                System.IO.File.Move(file, destination);
            }
            return UtilityResponse.Ok(new{restored = true});
        }

        catch (Exception ex){
            return UtilityResponse.Fail($"Restore failed: {ex.Message}");
        }

        finally{
            if (Directory.Exists(stagingDirectory)){Directory.Delete(stagingDirectory, true);}
        }
    }

    // ROTATE BACKUPS
    public static void RotateBackups(){
        DirectoryInfo directory = new DirectoryInfo(PassCorePaths.BackupDirectory);
        FileInfo[] backups = directory.GetFiles("*.zip").OrderBy(x => x.CreationTimeUtc).ToArray();

        while (backups.Length > MaxBackups){
            backups[0].Delete();
            backups = backups.Skip(1).ToArray();
        }
    }
}