using System.IO.Compression;
namespace PassCore.Utilities.File;
public sealed class AddFile{
    public static void AddTo(ZipArchive archive, string source, string archiveName){

        ZipArchiveEntry entry = archive.CreateEntry(archiveName, CompressionLevel.Optimal);
        using Stream sourceStream = System.IO.File.OpenRead(source);
        using Stream destination = entry.Open();

        sourceStream.CopyTo(destination);
    }
}