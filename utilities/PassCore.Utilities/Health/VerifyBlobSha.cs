using System.Text.Json;
using PassCore.Utilities.Core;

namespace PassCore.Utilities.Health;

public sealed class VerifyBlobSha{
    // NOTE VERIFICATION
    public static bool Blobsha256(JsonElement meta){
        try{
            foreach (var note in HealthService.EnumerateNotes(meta)){
                if (!HealthService.TryLoadNoteMetadata(note.NoteId, out _, out JsonDocument? document)){return false;}

                using (document){
                    JsonElement blobs = document!.RootElement.GetProperty("blobs");

                    foreach (var blob in blobs.EnumerateObject()){
                        string container = blob.Value.GetProperty("container").GetString()!;
                        string expected = blob.Value.GetProperty("sha256").GetString()!;
                        string path = Path.Combine(PassCorePaths.NotesContainerDirectory, note.NoteId, container, blob.Name);

                        if (!System.IO.File.Exists(path)){return false;}

                        string actual = HealthService.CalculateSha256(path);

                        if (!string.Equals(actual, expected, StringComparison.OrdinalIgnoreCase)){
                            return false;
                        }
                    }
                }
            }

            return true;
        }
        catch{
            return false;
        }
    }

    // IMAGE VERIFICATION
    public static bool ImgBlobSha256(JsonElement meta){
        try{
            foreach (var image in HealthService.EnumerateImages(meta)){
                if (!image.Info.TryGetProperty("uuid", out JsonElement uuidElement)){return false;}
                string? uuid = uuidElement.GetString();

                if (uuid is null){return false;}

                if (!HealthService.TryLoadImageMetadata(image.AlbumId, uuid, out _, out JsonDocument? document)){return false;}

                using (document){
                    JsonElement blobs = document!.RootElement.GetProperty("blobs");

                    foreach (var blob in blobs.EnumerateObject()){
                        string container = blob.Value.GetProperty("container").GetString()!;
                        string expected = blob.Value.GetProperty("sha256").GetString()!;
                        string path = Path.Combine(PassCorePaths.ImageContainerDirectory, image.AlbumId, uuid, container, blob.Name);

                        if (!System.IO.File.Exists(path)){return false;}

                        string actual = HealthService.CalculateSha256(path);

                        if (!string.Equals(actual, expected, StringComparison.OrdinalIgnoreCase)){
                            return false;
                        }
                    }
                }
            }
            return true;
        }

        catch{
            return false;
        }
    }
}