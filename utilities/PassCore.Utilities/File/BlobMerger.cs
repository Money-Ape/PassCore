using System;
using System.Text.Json.Nodes;
using PassCore.Utilities.Core;
using PassCore.Utilities.Models;
namespace PassCore.Utilities.File;

public static class BlobMerger{

    // ---- Public entry points ----------------------------------------

    // Raw merge given an explicit container directory (existing behavior).
    public static UtilityResponse Merge(string containerDirectory, string outputPath){
        return MergeCore(containerDirectory, outputPath);
    }

    /// <summary>Resolve a note's blob container from notes_index.json by title, then merge.</summary>
    public static UtilityResponse MergeNote(string title, string outputPath){
        try{
            if (string.IsNullOrWhiteSpace(title))
                throw new ArgumentException("Note title is required.", nameof(title));

            string notesIndexPath = PassCorePaths.NotesMetaData;

            if (!System.IO.File.Exists(notesIndexPath))
                throw new FileNotFoundException($"notes_index.json not found: {notesIndexPath}");

            JsonNode? root = JsonNode.Parse(System.IO.File.ReadAllText(notesIndexPath));
            JsonObject? notes = root?["notes"]?.AsObject();

            if (notes is null || !notes.TryGetPropertyValue(title, out JsonNode? noteEntryNode) || noteEntryNode is null)
                throw new KeyNotFoundException($"Note not found in index: {title}");

            JsonObject noteEntry = noteEntryNode.AsObject();

            if (noteEntry.Count == 0)
                throw new InvalidDataException($"Note entry for '{title}' has no UUID.");

            string noteUuid = noteEntry.First().Key;

            string? storagePath = root?["storage_path"]?.GetValue<string>();
            string notesRoot = string.IsNullOrWhiteSpace(storagePath) ? PassCorePaths.NotesContainerDirectory : storagePath;

            string containerDirectory = Path.Combine(notesRoot, noteUuid);

            return MergeCore(containerDirectory, outputPath);
        }
        catch (Exception ex){ return UtilityResponse.Fail(ex.Message); }
    }

    // Resolve an image's blob container from images_index.json by album + filename, then merge.
    public static UtilityResponse MergeImage(string albumName, string filename, string outputPath){
        try{
            if (string.IsNullOrWhiteSpace(albumName))
                throw new ArgumentException("Album name is required.", nameof(albumName));

            if (string.IsNullOrWhiteSpace(filename))
                throw new ArgumentException("Image filename is required.", nameof(filename));

            string imagesIndexPath = PassCorePaths.ImagesMetaData;

            if (!System.IO.File.Exists(imagesIndexPath))
                throw new FileNotFoundException($"images_index.json not found: {imagesIndexPath}");

            JsonNode? root = JsonNode.Parse(System.IO.File.ReadAllText(imagesIndexPath));
            JsonObject? albums = root?["albums"]?.AsObject();

            if (albums is null || !albums.TryGetPropertyValue(albumName, out JsonNode? albumEntryNode) || albumEntryNode is null)
                throw new KeyNotFoundException($"Album not found in index: {albumName}");

            JsonObject albumEntry = albumEntryNode.AsObject();

            if (albumEntry.Count == 0)
                throw new InvalidDataException($"Album '{albumName}' has no UUID.");

            var albumKvp = albumEntry.First();
            string albumUuid = albumKvp.Key;
            JsonObject? images = albumKvp.Value?.AsObject();

            if (images is null || !images.TryGetPropertyValue(filename, out JsonNode? imageEntryNode) || imageEntryNode is null)
                throw new KeyNotFoundException($"Image not found in album '{albumName}': {filename}");

            string? imageUuid = imageEntryNode["uuid"]?.GetValue<string>();

            if (string.IsNullOrWhiteSpace(imageUuid))
                throw new InvalidDataException($"Image entry for '{filename}' is missing its uuid.");

            // images_index.json has no storage_path of its own; the container
            // root is fixed per-OS via PassCorePaths.
            string containerDirectory = Path.Combine(PassCorePaths.ImageContainerDirectory, albumUuid, imageUuid);

            return MergeCore(containerDirectory, outputPath);
        }
        catch (Exception ex){ return UtilityResponse.Fail(ex.Message); }
    }

    // ---- Shared merge logic -------------------------------------------

    private static UtilityResponse MergeCore(string containerDirectory, string outputPath){
        try{

            if (string.IsNullOrWhiteSpace(containerDirectory))
                throw new ArgumentException("Container directory is required.", nameof(containerDirectory));

            if (string.IsNullOrWhiteSpace(outputPath))
                throw new ArgumentException("Output path is required.", nameof(outputPath));

            string sourceDirectory = Path.GetFullPath(ExpandHome(containerDirectory));
            string destination = Path.GetFullPath(ExpandHome(outputPath));

            if (!Directory.Exists(sourceDirectory))
                throw new DirectoryNotFoundException($"Container directory not found: {sourceDirectory}");

            string? destinationParent = Path.GetDirectoryName(destination);

            if (!string.IsNullOrEmpty(destinationParent))
                Directory.CreateDirectory(destinationParent);

            string metadataPath = Path.Combine(sourceDirectory, "metadata.json");

            if (!System.IO.File.Exists(metadataPath))
                throw new FileNotFoundException($"metadata.json not found in: {sourceDirectory}");

            JsonNode? root = JsonNode.Parse(System.IO.File.ReadAllText(metadataPath));
            JsonObject? blobsNode = root?["blobs"]?.AsObject();

            if (blobsNode is null || blobsNode.Count == 0)
                throw new InvalidDataException($"No blob entries found in metadata: {metadataPath}");

            var ordered = blobsNode
                .Select(kvp => new{
                    Filename = kvp.Key,
                    Container = kvp.Value?["container"]?.GetValue<string>() ?? throw new InvalidDataException($"Blob entry '{kvp.Key}' is missing its container."),
                    Index = ExtractBlobIndex(kvp.Key)
                }).OrderBy(b => b.Index).ToList();

            long totalSize = 0;

            /* Create/overwrite the destination. */
            using (FileStream output = new FileStream(
                    destination,
                    FileMode.Create,
                    FileAccess.Write,
                    FileShare.None,
                    bufferSize: 1024 * 1024,
                    options: FileOptions.SequentialScan)){
                byte[] buffer = new byte[1024 * 1024];

                foreach (var blob in ordered){
                    string blobPath = Path.Combine(sourceDirectory, blob.Container, blob.Filename);

                    if (!System.IO.File.Exists(blobPath))
                        throw new FileNotFoundException($"Missing blob referenced in metadata: {blobPath}");

                    using FileStream input = new FileStream(
                        blobPath,
                        FileMode.Open,
                        FileAccess.Read,
                        FileShare.Read,
                        bufferSize: 1024 * 1024,
                        options: FileOptions.SequentialScan);

                    int read;

                    while ((read = input.Read(buffer, 0, buffer.Length)) > 0){
                        output.Write(buffer, 0, read);
                        totalSize += read;
                    }
                }
                output.Flush(true);
            }

            /* Verify the merged file exists and has the expected size. */
            FileInfo resultInfo = new FileInfo(destination);

            if (!resultInfo.Exists)
                throw new IOException("Merged binary was not created.");

            if (resultInfo.Length != totalSize)
                throw new IOException($"Merged binary size mismatch. " + $"Expected {totalSize}, " + $"got {resultInfo.Length}.");

            long? expectedSize = root?["encrypted_size"]?.GetValue<long>();
            if (expectedSize is long expected && expected > 0 && resultInfo.Length != expected)
                throw new IOException($"Merged binary does not match recorded size. " + $"Expected {expected}, " + $"got {resultInfo.Length}.");

            return UtilityResponse.Ok(new{
                Path = destination,
                Size = totalSize,
                BlobCount = ordered.Count}
            );
        }
        catch (Exception ex){return UtilityResponse.Fail(ex.Message);}
    }

    private static int ExtractBlobIndex(string filename){
        string name = Path.GetFileNameWithoutExtension(filename);
        int lastUnderscore = name.LastIndexOf('_');

        if (lastUnderscore < 0 || lastUnderscore == name.Length - 1)
            throw new InvalidDataException($"Cannot determine blob order from filename: {filename}");

        string indexPart = name[(lastUnderscore + 1)..];

        if (!int.TryParse(indexPart, out int index))
            throw new InvalidDataException($"Cannot determine blob order from filename: {filename}");

        return index;
    }

    private static string ExpandHome(string path){
        if (path.Length == 1 && path == "~")
            return Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);

        if (path.Length > 1 && path[0] == '~' && (path[1] == '/' || path[1] == '\\'))
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), path[2..]);

        return path;
    }
}