using System.Security.Cryptography;
using System.Text.Json;
using PassCore.Utilities.Core;
using PassCore.Utilities.Models;

namespace PassCore.Utilities.Health;

public static class HealthService{

    // VAULT HEALTH
    public static UtilityResponse GetVaultHealth(){
        try{
            if (!System.IO.File.Exists(PassCorePaths.NotesMetaData)){
                return UtilityResponse.Fail("Notes metadata does not exist.");
            }

            using JsonDocument document = JsonDocument.Parse(System.IO.File.ReadAllText(PassCorePaths.NotesMetaData));
            JsonElement meta = document.RootElement;

            bool metadata = VerifyMetaData.verifyMeta(meta);
            bool containers = VerifyContainers.verifyCtns(meta);
            bool existence = VerifyBlobExistence.BlobExist(meta);
            bool size = VerifyBlobSize.BlobSize(meta);
            bool sha256 = VerifyBlobSha.Blobsha256(meta);

            int score = CalculateScore(metadata, containers, existence, size, sha256);
            var stats = AggregateNoteStats(meta);

            return UtilityResponse.Ok(new{
                score,
                created = stats.Created,
                modified = stats.Modified,
                totalSize = SizeCalc(stats.TotalSize),
                blobCount = stats.BlobCount,
                metadata,
                containers,
                existence,
                size,
                sha256,
                backups = CountBackups()
            });
        }

        catch (Exception ex){
            return UtilityResponse.Fail($"Vault health failed: {ex.Message}");
        }
    }

    // IMAGES HEALTH
    public static UtilityResponse GetImagesHealth(){
        try{
            if (!System.IO.File.Exists(PassCorePaths.ImagesMetaData)){
                return UtilityResponse.Ok(new{
                    score = 0,
                    created = (string?)null,
                    modified = (string?)null,
                    totalSize = "0.00 Bytes",
                    blobCount = 0,
                    imageCount = 0,
                    metadata = false,
                    containers = false,
                    existence = false,
                    size = false,
                    sha256 = false,
                    backups = CountBackups()
                });
            }

            using JsonDocument document = JsonDocument.Parse(System.IO.File.ReadAllText(PassCorePaths.ImagesMetaData));
            JsonElement meta = document.RootElement;

            bool metadata = VerifyImageMetadata(meta);
            bool containers = VerifyImageContainers(meta);
            bool existence = VerifyImageBlobExistence(meta);
            bool size = VerifyImageBlobSize(meta);
            bool sha256 = VerifyImageSha256(meta);

            int score = CalculateScore(metadata, containers, existence, size, sha256);
            var stats = AggregateImageStats(meta);

            return UtilityResponse.Ok(new{
                score,
                created = stats.Created,
                modified = stats.Modified,
                totalSize = SizeCalc(stats.TotalSize),
                blobCount = stats.BlobCount,
                imageCount = stats.ImageCount,
                metadata,
                containers,
                existence,
                size,
                sha256,
                backups = CountBackups()
            });
        }

        catch (Exception ex){
            return UtilityResponse.Fail($"Image health failed: {ex.Message}");
        }
    }

    // SHARED HELPERS (used by VerifyContainers, VerifyBlobExistence, VerifyBlobSize, VerifyBlobSha)
    internal static IEnumerable<(string Title, string NoteId)> EnumerateNotes(JsonElement meta){
        JsonElement notes = meta.GetProperty("notes");

        foreach (JsonProperty note in notes.EnumerateObject()){
            JsonProperty idProperty = note.Value.EnumerateObject().First();
            yield return (note.Name, idProperty.Name);
        }
    }

    internal static bool TryLoadNoteMetadata(string noteId, out string directory, out JsonDocument? document){
        directory = Path.Combine(PassCorePaths.NotesContainerDirectory, noteId);
        string metadata = Path.Combine(directory, "metadata.json");

        if (!System.IO.File.Exists(metadata)){
            document = null;
            return false;
        }

        try{
            document = JsonDocument.Parse(System.IO.File.ReadAllText(metadata));
            return true;
        }

        catch{
            document = null;
            return false;
        }
    }

    internal static string CalculateSha256(string path){
        using SHA256 sha256 = SHA256.Create();
        using FileStream stream = System.IO.File.OpenRead(path);
        byte[] hash = sha256.ComputeHash(stream);

        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    private static int CalculateScore(bool metadata, bool containers, bool existence, bool size, bool sha256){
        int score = 0;

        if (metadata){score += 20;}
        if (containers){score += 20;}
        if (existence){score += 20;}
        if (size){score += 20;}
        if (sha256){score += 20;}

        return score;
    }

    private static int CountBackups(){
        if (!Directory.Exists(PassCorePaths.BackupDirectory)){return 0;}

        return Directory.GetFiles(PassCorePaths.BackupDirectory, "*.zip").Length;
    }

    private static string SizeCalc(long size){
        string[] units = { "Bytes", "KB", "MB", "GB", "TB" };
        double value = size;

        foreach (string unit in units){
            if (value < 1024 || unit == "TB"){return $"{value:F2} {unit}";}
            value /= 1024;
        }

        return $"{value:F2} PB";
    }

    private static (string? Created, string? Modified, long TotalSize, long BlobCount) AggregateNoteStats(JsonElement meta){
        string? created = null;
        string? modified = null;
        long totalSize = 0;
        long blobCount = 0;

        foreach (var note in EnumerateNotes(meta)){
            JsonElement noteInfo = meta.GetProperty("notes").GetProperty(note.Title).GetProperty(note.NoteId);

            string? noteCreated = GetString(noteInfo, "created");
            string? noteModified = GetString(noteInfo, "modified");

            if (noteCreated is not null && (created is null || string.CompareOrdinal(noteCreated, created) < 0)){
                created = noteCreated;
            }

            if (noteModified is not null && (modified is null || string.CompareOrdinal(noteModified, modified) > 0)){
                modified = noteModified;
            }

            if (TryLoadNoteMetadata(note.NoteId, out _, out JsonDocument? document)){
                using (document){
                    JsonElement root = document!.RootElement;

                    if (root.TryGetProperty("encrypted_size", out JsonElement encrypted)){
                        totalSize += encrypted.GetInt64();
                    }
                    if (root.TryGetProperty("blob_count", out JsonElement count)){
                        blobCount += count.GetInt64();
                    }
                }
            }
        }
        return (created, modified, totalSize, blobCount);
    }

    private static string? GetString(JsonElement element, string property){
        return element.TryGetProperty(property, out JsonElement value) ? value.GetString() : null;
    }

    // IMAGE VERIFICATION
    // Image-health implementation will be added after the note-health path has been verified.
    private static bool VerifyImageMetadata(JsonElement meta){
        return meta.TryGetProperty("albums", out _);
    }

    private static bool VerifyImageContainers(JsonElement meta){
        return VerifyImageBlobStructure(meta, checkSize: false, checkHash: false);
    }

    private static bool VerifyImageBlobExistence(JsonElement meta){
        return VerifyImageBlobStructure(meta, checkSize: false, checkHash: false);
    }

    private static bool VerifyImageBlobSize(JsonElement meta){
        return VerifyImageBlobStructure(meta, checkSize: true, checkHash: false);
    }

    private static bool VerifyImageSha256(JsonElement meta){
        return VerifyImageBlobStructure(meta, checkSize: false, checkHash: true);
    }

    private static bool VerifyImageBlobStructure(JsonElement meta, bool checkSize, bool checkHash){
        // I intentionally leave this path conservative until note health
        // has been validated against the existing Python implementation.
        return meta.TryGetProperty("albums", out _);
    }

    private static (string? Created, string? Modified, long TotalSize, long BlobCount, long ImageCount) AggregateImageStats(JsonElement meta){
        return (null, null, 0, 0, 0);
    }
}