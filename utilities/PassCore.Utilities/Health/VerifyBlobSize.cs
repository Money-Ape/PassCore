using System.Text.Json;
using PassCore.Utilities.Core;

namespace PassCore.Utilities.Health;

public sealed class VerifyBlobSize{
    public static bool BlobSize(JsonElement meta){
        try{
            foreach (var note in HealthService.EnumerateNotes(meta)){
                if (!HealthService.TryLoadNoteMetadata(note.NoteId, out _, out JsonDocument? document)){return false;}

                using (document){
                    JsonElement blobs = document!.RootElement.GetProperty("blobs");

                    foreach (var blob in blobs.EnumerateObject()){
                        string container = blob.Value.GetProperty("container").GetString()!;
                        long expected = blob.Value.GetProperty("size").GetInt64();
                        string path = Path.Combine(PassCorePaths.NotesContainerDirectory, note.NoteId, container, blob.Name);

                        if (!System.IO.File.Exists(path) || new FileInfo(path).Length != expected){
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