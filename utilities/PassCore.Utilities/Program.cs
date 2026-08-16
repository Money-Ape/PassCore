using System.Text.Json;
using PassCore.Utilities.Backup;
using PassCore.Utilities.Core;
using PassCore.Utilities.File;
using PassCore.Utilities.Health;
using PassCore.Utilities.Models;

namespace PassCore.Utilities;

public static class Program{
    private static readonly JsonSerializerOptions JsonOptions = new(){
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
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
            "backup_create" => BackupService.Create(request.Force),
            "backup_restore" => BackupService.Restore(request.Path),
            "vault_export" => VaultFileService.ExportPcv(request.Destination),
            "vault_import" => VaultFileService.ImportPcv(request.Path),

            _ => UtilityResponse.Fail($"Unknown operation: {request.Operation}")
        };
    }
}