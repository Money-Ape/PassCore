using System.IO.Compression;
using PassCore.Utilities.Core;
using PassCore.Utilities.Models;

namespace PassCore.Utilities.File;

public static class VaultFileService{

    // EXPORT PCV
    public static UtilityResponse ExportPcv(string? destination){
        try{
            if (string.IsNullOrWhiteSpace(destination)){
                return UtilityResponse.Fail("Export destination was not provided.");
            }
            if (!System.IO.File.Exists(PassCorePaths.NotesMetaData)){
                return UtilityResponse.Fail("No vault available to export.");
            }
            if (!destination.EndsWith(".pcv", StringComparison.OrdinalIgnoreCase)){
                destination += ".pcv";
            }

            using FileStream stream = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None);
            using ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Create);

            AddFile.AddTo(archive, PassCorePaths.SaltFile, Path.GetFileName(PassCorePaths.SaltFile));
            AddFile.AddTo(archive, PassCorePaths.ImagesMetaData, Path.GetFileName(PassCorePaths.ImagesMetaData));
            AddFile.AddTo(archive, PassCorePaths.NotesMetaData, Path.GetFileName(PassCorePaths.NotesMetaData));
            AddFile.AddTo(archive, PassCorePaths.SettingsFile, Path.GetFileName(PassCorePaths.SettingsFile));

            AddContainerFiles(archive);

            return UtilityResponse.Ok(new{path = destination});
        }

        catch (Exception ex){
            return UtilityResponse.Fail($"Export Failed: {ex.Message}");
        }
    }

    // IMPORT PCV
    public static UtilityResponse ImportPcv(string? source){
        try{
            if (string.IsNullOrWhiteSpace(source)){
                return UtilityResponse.Fail("Import source was not provided.");
            }
            if (!System.IO.File.Exists(source)){
                return UtilityResponse.Fail("PCV file does not exist.");
            }

            string staging = Path.Combine(Path.GetTempPath(), $"passcore-pcv-{Guid.NewGuid():N}");

            try{
                Directory.CreateDirectory(staging);
                ZipFile.ExtractToDirectory(source, staging);
                string[] required = {
                    "vault.salt",
                    "images_index.json",
                    "notes_index.json",
                    "settings.yaml"
                };
                foreach (string file in required){
                    if (!System.IO.File.Exists(Path.Combine(staging, file))){
                        return UtilityResponse.Fail($"Invalid PCV: missing {file}");
                    }
                }

                // Existing import behavior replaces the current vault.
                DeleteDirectoryContents.DDC(PassCorePaths.ContainerDirectory);
                Directory.CreateDirectory(PassCorePaths.ContainerDirectory);

                MoveFile.Move(Path.Combine(staging, "vault.salt"), PassCorePaths.SaltFile);
                MoveFile.Move(Path.Combine(staging, "images_index.json"), PassCorePaths.ImagesMetaData);
                MoveFile.Move(Path.Combine(staging, "notes_index.json"), PassCorePaths.NotesMetaData);
                MoveFile.Move(Path.Combine(staging, "settings.yaml"), PassCorePaths.SettingsFile);

                foreach (string file in Directory.EnumerateFiles(staging, "*", System.IO.SearchOption.AllDirectories)){
                    string relative = Path.GetRelativePath(staging, file);
                    
                    if (required.Contains(relative, StringComparer.Ordinal)){continue;}

                    string destination = Path.Combine(PassCorePaths.ContainerDirectory, relative);
                    string? parent = Path.GetDirectoryName(destination);
                    if (parent is not null){Directory.CreateDirectory(parent);}

                    System.IO.File.Move(file, destination);
                }
                return UtilityResponse.Ok(new{imported = true});
            }

            finally{
                if (Directory.Exists(staging)){Directory.Delete(staging, true);}
            }
        }

        catch(Exception ex){
            return UtilityResponse.Fail($"Import failed: {ex.Message}");
        }
    }

    // ADD CONTAINER FILES
    private static void AddContainerFiles(ZipArchive archive){
        if (!Directory.Exists(PassCorePaths.ContainerDirectory)){return;}

        foreach (string file in Directory.EnumerateFiles(PassCorePaths.ContainerDirectory, "*", System.IO.SearchOption.AllDirectories)){
            string relative = Path.GetRelativePath(PassCorePaths.ContainerDirectory, file);

            AddFile.AddTo(archive, file, relative);
        }
    }
}