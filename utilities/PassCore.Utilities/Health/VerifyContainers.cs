using System.Text.Json;
using PassCore.Utilities.Core;

namespace PassCore.Utilities.Health;

public sealed class VerifyContainers{
    // NOTE VERIFICATION
    public static bool verifyCtns(JsonElement meta){
        try{
            foreach (var note in HealthService.EnumerateNotes(meta)){
                string directory = Path.Combine(PassCorePaths.NotesContainerDirectory, note.NoteId);

                if (!Directory.Exists(directory) || !System.IO.File.Exists(Path.Combine(directory, "metadata.json"))){
                    return false;
                }
            }

            return true;
        }
        catch{
            return false;
        }
    }

    // IMAGE VERIFICATION
    public static bool VerifyImgCtns(JsonElement meta){
        try{
            foreach (var image in HealthService.EnumerateImages(meta)){
                if (!image.Info.TryGetProperty("uuid", out JsonElement uuidElement)){return false;}
                string? uuid = uuidElement.GetString();

                if (uuid is null){return false;}
                string imageDir = Path.Combine(PassCorePaths.ImageContainerDirectory, image.AlbumId, uuid);

                if (!Directory.Exists(imageDir) || !System.IO.File.Exists(Path.Combine(imageDir, "metadata.json"))){
                    return false;
                }
            }
            return true;
        }

        catch{
            return false;
        }
    }
}