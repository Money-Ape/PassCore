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
                total_size = SizeCalc(stats.TotalSize),
                blob_count = stats.BlobCount,
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
                    total_size = 0,
                    blob_count = 0,
                    image_count = 0,
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

            bool metadata = VerifyMetaData.VerifyImgMeta(meta);
            bool containers = VerifyContainers.VerifyImgCtns(meta);
            bool existence = VerifyBlobExistence.ImgBlobExist(meta);
            bool size = VerifyBlobSize.ImgBlobSize(meta);
            bool sha256 = VerifyBlobSha.ImgBlobSha256(meta);

            int score = CalculateScore(metadata, containers, existence, size, sha256);
            var stats = AggregateImageStats(meta);

            return UtilityResponse.Ok(new{
                score,
                created = stats.Created,
                modified = stats.Modified,
                total_size = SizeCalc(stats.TotalSize),
                blob_count = stats.BlobCount,
                image_count = stats.ImageCount,
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

    internal static IEnumerable<(string AlbumName, string AlbumId, string Filename, JsonElement Info)> EnumerateImages(JsonElement meta){
        if (!meta.TryGetProperty("albums", out JsonElement albums)){yield break;}

        foreach (JsonProperty album in albums.EnumerateObject()){
            JsonElement albumObject = album.Value;

            string? albumId = null;
            JsonElement images = default;

            foreach (JsonProperty idProperty in albumObject.EnumerateObject()){
                albumId = idProperty.Name;
                images = idProperty.Value;
                break;
            }

            if (albumId is null){continue;}

            foreach (JsonProperty image in images.EnumerateObject()){
                yield return (album.Name, albumId, image.Name, image.Value);
            }
        }
    }

    // Mirrors health.py's _load_image_meta.
    internal static bool TryLoadImageMetadata(string albumId, string imageId, out string directory, out JsonDocument? document){
        directory = Path.Combine(PassCorePaths.ImageContainerDirectory, albumId, imageId);
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

    private static (string? Created, string? Modified, long TotalSize, long BlobCount, long ImageCount) AggregateImageStats(JsonElement meta){
        string? created = null;
        string? modified = null;
        long totalSize = 0;
        long blobCount = 0;
        long imageCount = 0;

        foreach (var image in EnumerateImages(meta)){
            imageCount++;

            string? imgCreated = GetString(image.Info, "created_at");
            string? imgModified = GetString(image.Info, "modified") ?? imgCreated;

            if (imgCreated is not null && (created is null || string.CompareOrdinal(imgCreated, created) < 0)){
                created = imgCreated;
            }
            if (imgModified is not null && (modified is null || string.CompareOrdinal(imgModified, modified) > 0)){
                modified = imgModified;
            }

            if (!image.Info.TryGetProperty("uuid", out JsonElement uuidElement)){continue;}
            string? uuid = uuidElement.GetString();
            if (uuid is null){continue;}

            if (TryLoadImageMetadata(image.AlbumId, uuid, out _, out JsonDocument? document)){
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
        return (created, modified, totalSize, blobCount, imageCount);
    }

    private static string? GetString(JsonElement element, string property){
        return element.TryGetProperty(property, out JsonElement value) ? value.GetString() : null;
    }
}