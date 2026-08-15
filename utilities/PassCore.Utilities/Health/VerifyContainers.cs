using System.Text.Json;
using PassCore.Utilities.Core;

namespace PassCore.Utilities.Health;

public sealed class VerifyContainers{
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
}