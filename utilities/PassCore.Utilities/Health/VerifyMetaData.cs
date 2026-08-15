using System.Text.Json;
namespace PassCore.Utilities.Health;

public sealed class VerifyMetaData{
    // NOTE VERIFICATION
    public static bool verifyMeta(JsonElement meta){
        try{
            if (!meta.TryGetProperty("notes", out JsonElement notes)){return false;}

            foreach (JsonProperty note in notes.EnumerateObject()){
                JsonElement noteObject = note.Value;

                string noteId = noteObject.EnumerateObject().First().Name;

                JsonElement noteInfo = noteObject.GetProperty(noteId);

                if (!noteInfo.TryGetProperty("created", out _) || !noteInfo.TryGetProperty("modified", out _)){return false;}
            }
            return true;
        }

        catch{return false;}
    }
}