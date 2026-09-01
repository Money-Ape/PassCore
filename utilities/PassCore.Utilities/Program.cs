using System.Text.Json;
using PassCore.Utilities.Backup;
using PassCore.Utilities.Core;
using PassCore.Utilities.File;
using PassCore.Utilities.Health;
using PassCore.Utilities.Models;

namespace PassCore.Utilities;

public static class Program{
    private static readonly JsonSerializerOptions JsonOptions = new(){
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
    };
    
    public static int Main(){
        try{
            PassCorePaths.EnsureDirectories();
            string? line;
            while ((line = Console.ReadLine()) is not null){
                if (string.IsNullOrWhiteSpace(line)){continue;}
                UtilityResponse response;

                try{
                    UtilityRequest? request = JsonSerializer.Deserialize<UtilityRequest>(line, JsonOptions);
                    if (request is null){
                        response = UtilityResponse.Fail("Invalid utility request.!");
                    }
                    else{
                        response = Dispatch(request);
                    }
                }
                catch (Exception ex){
                    response = UtilityResponse.Fail(ex.Message);
                }
                Console.WriteLine(JsonSerializer.Serialize(response, JsonOptions));
                Console.Out.Flush();
            }
            return 0;
        }
        catch (Exception ex){
            Console.Error.WriteLine(ex);
            return 1;
        }
    }

    public static UtilityResponse Dispatch(UtilityRequest request){
        return request.Operation switch{
            "vault_health" => HealthService.GetVaultHealth(),
            "images_health" => HealthService.GetImagesHealth(),

            "backup_mark_changed" => BackupService.MarkVaultChanged(),
            "backup_create" => BackupService.Create(request.Force),
            "backup_restore" => BackupService.Restore(request.Path),

            "vault_export" => VaultFileService.ExportPcv(request.Destination),
            "vault_import" => VaultFileService.ImportPcv(request.Path),

            "merge_blob_bin" => request.ContainerDirectory is not null && request.OutputPath is not null
                    ? BlobMerger.Merge(request.ContainerDirectory, request.OutputPath) : UtilityResponse.Fail("container_directory and output_path are required."),

            "merge_note_blob" => request.NoteTitle is not null && request.OutputPath is not null
                    ? BlobMerger.MergeNote(request.NoteTitle, request.OutputPath) : UtilityResponse.Fail("note_title and output_path are required."),

            "merge_image_blob" => request.AlbumName is not null && request.ImageFilename is not null && request.OutputPath is not null
                    ? BlobMerger.MergeImage(request.AlbumName, request.ImageFilename, request.OutputPath) : UtilityResponse.Fail("album_name, image_filename and output_path are required."),

            _ => UtilityResponse.Fail($"Unknown operation: {request.Operation}")
        };
    }
}